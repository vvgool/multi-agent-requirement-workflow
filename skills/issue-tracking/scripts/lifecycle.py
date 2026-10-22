#!/usr/bin/env python3
"""Read-only lifecycle contract checks. No network, scheduler, or state writes.

JSON CLI: lifecycle.py {config,target,authorization,release,close,confirmation,recovery,comment,outcome,key} FILE
Evidence references and read conclusions MUST come from coordinator verification;
passing this structural gate does not establish external facts or write authority.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from datetime import datetime
from urllib.parse import urlsplit, unquote

LEGACY_EVENTS = frozenset(('issue_bound revision_started requirement_review_ready '
                          'requirement_approved development_ready testing_failed '
                          'workflow_blocked workflow_unblocked feature_completed').split())
EVENTS = LEGACY_EVENTS | frozenset(('development_started testing_started repair_started '
                                  'workflow_waiting_user release_succeeded release_failed '
                                  'release_rolled_back delivery_confirmed').split())
TARGET_FIELDS = ('provider', 'host', 'repository', 'issue_number')


class Invalid(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Invalid(reason)


def obj(value, label):
    require(isinstance(value, dict), label + '_object_required')
    return value


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value):
    return isinstance(value, list) and bool(value) and all(nonempty(x) for x in value)


def config(value):
    value = obj(value, 'config')
    defaults = dict(binding='off', sync='off', close='off')
    require(not set(value) - set(defaults), 'unknown_config_field')
    result = dict(defaults, **value)
    for field, choices in [('binding', ('off', 'optional', 'required')),
                           ('sync', ('off', 'milestones')), ('close', ('off', 'after_release'))]:
        require(type(result[field]) is str and result[field] in choices, 'invalid_' + field)
    require(result['binding'] != 'off' or (result['sync'] == result['close'] == 'off'),
            'binding_off_with_remote_policy')
    require(result['sync'] != 'off' or result['close'] == 'off', 'sync_off_with_after_release')
    return result


def target(value):
    value = obj(value, 'target')
    require(all(k in value for k in TARGET_FIELDS), 'incomplete_target')
    require(value['provider'] in ('github', 'gitlab'), 'unsupported_issue_provider')
    require(nonempty(value['host']) and re.fullmatch(r'[a-z0-9.-]+(?::[0-9]+)?', value['host']), 'invalid_host')
    repo = value['repository']
    require(nonempty(repo) and all(re.fullmatch(r'[A-Za-z0-9_.-]+', x) and x not in ('.', '..')
                                  for x in repo.split('/')) and len(repo.split('/')) >= 2,
            'invalid_repository')
    require(value['provider'] != 'github' or len(repo.split('/')) == 2, 'invalid_github_repository')
    require(type(value['issue_number']) is int and value['issue_number'] > 0, 'invalid_issue_number')
    require(not value.get('pull_request') and not value.get('merge_request'), 'not_an_issue')
    if 'url' in value:
        u = urlsplit(value['url'])
        require(u.scheme == 'https' and not u.username and not u.password and
                u.netloc == value['host'] and not u.query and not u.fragment, 'invalid_issue_url')
        path = unquote(u.path).rstrip('/')
        expected = '/' + repo + ('/issues/' if value['provider'] == 'github' else '/-/issues/') + str(value['issue_number'])
        # Prefixed self-hosted instances require a previously verified configured prefix.
        prefix = value.get('verified_path_prefix', '')
        require(type(prefix) is str and (prefix == '' or (prefix.startswith('/') and '..' not in prefix.split('/'))), 'invalid_path_prefix')
        require(path == prefix.rstrip('/') + expected, 'issue_url_identity_conflict')
    return {k: value[k] for k in TARGET_FIELDS}


def same_target(a, b):
    return target(a) == target(b)


def authorization(value):
    """Input: authorization, binding, feature_id, baseline_id, operation, optional event/history."""
    value = obj(value, 'authorization_context')
    a = obj(value.get('authorization'), 'authorization')
    require(same_target(a.get('target'), value.get('binding')), 'authorization_target_mismatch')
    require(a.get('revoked', False) is False, 'authorization_revoked')
    require(nonempty(a.get('user_response')) and nonempty(a.get('confirmed_at')), 'authorization_evidence_missing')
    operation = value.get('operation')
    require(operation in ('comment', 'close'), 'invalid_operation')
    if a.get('scope') == 'milestone_comments':
        require(operation == 'comment' and value.get('event_kind') in LEGACY_EVENTS, 'legacy_authorization_not_extended')
        require(not value.get('historical'), 'history_authorization_required')
        # Legacy ownership remains the containing feature record, never a cross-feature grant.
        require(value.get('legacy_owner_feature_id') == value.get('feature_id') and
                nonempty(value.get('feature_id')), 'legacy_feature_ownership_required')
        return {'allowed': True, 'legacy': True}
    require(a.get('schema_version') == 2, 'unknown_authorization_schema')
    require(a.get('feature_id') == value.get('feature_id') and nonempty(a.get('feature_id')), 'authorization_feature_mismatch')
    require(type(a.get('include_future_revisions')) is bool, 'invalid_revision_authorization')
    require(nonempty(a.get('baseline_id')) and
            (a['baseline_id'] == value.get('baseline_id') or a['include_future_revisions']), 'authorization_baseline_mismatch')
    require(nonempty(a.get('scope_description')), 'authorization_scope_missing')
    if value.get('scope_description') is not None:
        require(a['scope_description'] == value['scope_description'] or
                (a['include_future_revisions'] and value.get('future_scope_covered') is True), 'authorization_scope_mismatch')
    ops = a.get('operations')
    require(isinstance(ops, list) and bool(ops) and not set(ops) - {'comment', 'close'}, 'invalid_operations')
    require(operation in ops, 'operation_not_authorized')
    require(a.get('close_policy') in ('off', 'after_release'), 'invalid_authorized_close_policy')
    kinds = a.get('event_kinds')
    require(isinstance(kinds, list) and all(type(k) is str and k in EVENTS for k in kinds), 'invalid_event_kinds')
    if operation == 'comment':
        require(value.get('event_kind') in kinds, 'event_not_authorized')
    if operation == 'close':
        require(a.get('full_issue_scope') is True and strings(a.get('scope_evidence')), 'full_scope_authorization_required')
    if value.get('historical'):
        require(value.get('event_id') in a.get('history_event_ids', []) and
                nonempty(value.get('original_occurred_at')) and nonempty(value.get('backfilled_at')),
                'history_authorization_or_time_missing')
    return {'allowed': True, 'legacy': False}


def release(value):
    value = obj(value, 'release_context')
    r = obj(value.get('release'), 'release')
    a = obj(value.get('acceptance'), 'acceptance')
    require(r.get('kind') in ('package', 'service', 'none'), 'invalid_release_kind')
    require(r['kind'] != 'none', 'no_release_requires_manual_choice')
    require(r.get('status') == 'succeeded', 'release_not_succeeded')
    require(all(nonempty(r.get(k)) for k in ('occurred_at', 'target', 'identity', 'commit_or_artifact', 'receipt')),
            'release_evidence_missing')
    require(r.get('receipt_readable') is True and r.get('published') is True, 'release_not_verified')
    for k in ('feature_id', 'baseline_id', 'delivery_id', 'code_baseline_digest'):
        require(nonempty(r.get(k)) and r[k] == a.get(k), 'release_' + k + '_mismatch')
    require(strings(value.get('scope_ids')) and strings(r.get('coverage')) and
            set(value['scope_ids']) <= set(r['coverage']), 'release_scope_incomplete')
    if r['kind'] == 'package':
        require(r.get('public') is True and r.get('draft') is False, 'package_not_public_final')
    else:
        require(nonempty(value.get('environment')) and r.get('environment') == value['environment'] and
                r.get('target') == value.get('environment') and r.get('runtime_verified') is True,
                'service_environment_not_verified')
    return {'verified': True}


def timestamp(value, reason):
    require(nonempty(value), reason)
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(result.tzinfo is not None and result.utcoffset() is not None, reason)
        return result
    except ValueError:
        raise Invalid(reason)


def confirmation(value):
    """Verify a current final completion record, distinct from approval/permission.

    Evidence contents must be read by the coordinator; this checks their explicit
    binding and chronology, never infers a user's intent from an isolated word.
    """
    value = obj(value, 'confirmation_context')
    a = obj(value.get('acceptance'), 'acceptance')
    require(a.get('status') == 'passed' and a.get('independent') is True and nonempty(a.get('evidence')),
            'independent_acceptance_required')
    req = obj(value.get('completion_requirements'), 'completion_requirements')
    require(nonempty(req.get('evidence')) and
            all(req.get(k) == value.get(k) and nonempty(req.get(k)) for k in ('feature_id', 'baseline_id')),
            'completion_requirements_identity_or_evidence_missing')
    require(strings(value.get('scope_ids')) and strings(req.get('scope_ids')) and
            set(req['scope_ids']) == set(value['scope_ids']), 'completion_requirements_scope_mismatch')
    require(type(req.get('release_required')) is bool and req.get('release_kind') in ('none', 'package', 'service'),
            'completion_requirements_release_applicability_missing')
    r = obj(value.get('release'), 'release')
    require(r.get('kind') == req['release_kind'], 'completion_requirements_release_kind_mismatch')
    require(r.get('status') in ('unknown', 'unpublished', 'succeeded', 'failed', 'partial', 'rolled_back', 'revoked', 'not_required'),
            'invalid_release_status')
    require(r['kind'] != 'none' or (r['status'] == 'not_required' and req['release_required'] is False),
            'none_is_not_a_release_object')
    require(r['kind'] == 'none' or r['status'] != 'not_required', 'package_service_status_must_remain_real')
    expected = req.get('required_acceptance_ids')
    results = a.get('acceptance_results')
    require(strings(expected) and len(expected) == len(set(expected)) and isinstance(results, list),
            'applicable_acceptance_coverage_missing')
    require(all(isinstance(x, dict) and nonempty(x.get('id')) for x in results), 'invalid_acceptance_result')
    ids = [x['id'] for x in results]
    require(len(ids) == len(set(ids)) and set(ids) == set(expected), 'applicable_acceptance_coverage_mismatch')
    require(all(x.get('status') == 'passed' and nonempty(x.get('evidence')) for x in results),
            'applicable_acceptance_not_passed')
    cf = obj(value.get('completion_confirmation'), 'completion_confirmation')
    require(cf.get('schema_version') == 1 and cf.get('kind') == 'delivery_completion', 'delivery_completion_required')
    for k in ('feature_id', 'baseline_id', 'delivery_id', 'code_baseline_digest'):
        require(nonempty(a.get(k)) and cf.get(k) == a[k] and
                (k not in ('feature_id', 'baseline_id') or a[k] == value.get(k)), 'confirmation_' + k + '_mismatch')
    require(nonempty(value.get('scope_description')) and cf.get('scope_description') == value['scope_description'],
            'confirmation_scope_description_mismatch')
    require(strings(cf.get('scope_ids')) and set(cf['scope_ids']) == set(value['scope_ids']), 'confirmation_scope_mismatch')
    require(same_target(cf.get('target'), value.get('binding')), 'confirmation_target_mismatch')
    require(all(nonempty(cf.get(k)) for k in ('event_id', 'user_response', 'response_evidence')), 'confirmation_response_evidence_missing')
    require(cf['event_id'].endswith(':delivery_confirmed'), 'confirmation_event_id_invalid')
    require(cf.get('source_session') is None or nonempty(cf['source_session']), 'confirmation_source_invalid')
    shown = obj(cf.get('presentation'), 'confirmation_presentation')
    require(nonempty(shown.get('evidence')) and nonempty(shown.get('delivery_summary')) and
            strings(shown.get('scope_coverage_evidence')), 'presentation_evidence_or_summary_missing')
    require(shown.get('acceptance_results') == results, 'presentation_acceptance_results_mismatch')
    for k in ('feature_id', 'baseline_id', 'delivery_id', 'code_baseline_digest', 'scope_description'):
        require(shown.get(k) == cf[k], 'presentation_' + k + '_mismatch')
    require(same_target(shown.get('target'), value.get('binding')), 'presentation_target_mismatch')
    require(strings(shown.get('scope_ids')) and set(shown['scope_ids']) == set(value['scope_ids']), 'presentation_scope_mismatch')
    require(shown.get('acceptance_evidence') == a['evidence'], 'presentation_acceptance_mismatch')
    require(shown.get('unresolved_items') == [], 'presentation_unresolved_items')
    require(shown.get('release_kind') == r['kind'] and shown.get('release_status') == r['status'] and
            type(shown.get('release_required')) is bool and shown['release_required'] == req['release_required'],
            'presentation_release_mismatch')
    impact = obj(shown.get('release_impact'), 'presentation_release_impact')
    require(impact.get('assessed') is True and strings(impact.get('evidence')) and impact.get('unresolved') == [],
            'release_impact_unresolved_or_unverified')
    passed = timestamp(a.get('passed_at'), 'confirmation_acceptance_time_missing')
    displayed = timestamp(shown.get('presented_at'), 'confirmation_presentation_time_missing')
    confirmed = timestamp(cf.get('confirmed_at'), 'confirmation_time_missing')
    require(passed <= displayed <= confirmed, 'confirmation_time_order_invalid')
    return dict(confirmed=True, event_id=cf['event_id'])


def close(value):
    value = obj(value, 'close_context')
    p = config(value.get('policy', {}))
    mode = value.get('mode')
    require(mode in ('automatic', 'manual'), 'invalid_close_mode')
    require(p['binding'] != 'off', 'binding_disabled')
    require(mode != 'automatic' or (p['sync'] == 'milestones' and p['close'] == 'after_release'), 'automatic_close_disabled')
    require(mode != 'manual' or value.get('manual_summary_authorized') is True, 'manual_summary_authorization_required')
    b = obj(value.get('binding'), 'binding')
    target(b)
    require(nonempty(b.get('url')) and nonempty(b.get('verified_at')), 'binding_not_verified')
    for op in ('comment', 'close'):
        ctx = dict(value, operation=op)
        if op == 'comment':
            # The necessary summaries below are checked against exact authorized events.
            ctx['event_kind'] = 'feature_completed'
        authorization(ctx)
    auth = value['authorization']
    require(mode != 'automatic' or auth.get('close_policy') == p['close'], 'close_policy_authorization_mismatch')
    require(value.get('approval_valid') is True, 'approval_not_valid')
    for field in ('active_write', 'pending_input', 'unfinished_changes'):
        require(value.get(field) is False, field + '_prevents_close')
    a = obj(value.get('acceptance'), 'acceptance')
    require(a.get('status') == 'passed' and a.get('independent') is True and nonempty(a.get('evidence')),
            'independent_acceptance_required')
    for field in ('feature_id', 'baseline_id'):
        require(nonempty(value.get(field)) and a.get(field) == value[field], 'acceptance_identity_mismatch')
    require(nonempty(a.get('delivery_id')) and nonempty(a.get('code_baseline_digest')), 'acceptance_baseline_missing')
    r = obj(value.get('release'), 'release')
    if mode == 'manual':
        confirmation(value)
    release_needed = mode == 'automatic' or value['completion_requirements']['release_required']
    if release_needed:
        release(value)
    coverage = obj(value.get('scope_coverage'), 'scope_coverage')
    require(coverage.get('mode') in ('exclusive', 'shared') and coverage.get('confirmed') is True and
            nonempty(coverage.get('inspected_at')) and strings(coverage.get('evidence')) and
            coverage.get('remaining') == [] and coverage.get('unknown') is False and
            strings(coverage.get('scope_ids')) and set(coverage['scope_ids']) == set(value['scope_ids']),
            'issue_scope_incomplete_or_unknown')
    comments = value.get('required_comments')
    require(isinstance(comments, list) and bool(comments), 'required_summaries_missing')
    required = {'progress', 'acceptance'}
    if mode == 'manual':
        required.add('confirmation')
    if release_needed:
        required.add('release')
    summary_events = {'progress': EVENTS - {'release_succeeded', 'release_failed', 'release_rolled_back', 'delivery_confirmed'},
                      'acceptance': {'feature_completed'}, 'release': {'release_succeeded'},
                      'confirmation': {'delivery_confirmed'}}
    covered = set()
    for c in comments:
        require(same_target(c.get('target'), b) and c.get('status') == 'synced' and
                nonempty(c.get('receipt')) and nonempty(c.get('verified_at')), 'summary_not_verified')
        # A single verified comment may cover several separately evidenced facts.
        facts = c.get('facts', [c])
        require(isinstance(facts, list) and bool(facts), 'summary_facts_missing')
        for fact in facts:
            require(fact.get('kind') in summary_events and fact.get('event_kind') in summary_events[fact['kind']],
                    'summary_event_kind_mismatch')
            authorization(dict(value, operation='comment', event_kind=fact['event_kind']))
            if mode == 'manual':
                require(nonempty(fact.get('event_id')) and nonempty(fact.get('evidence')), 'summary_fact_evidence_missing')
                if fact['kind'] == 'confirmation':
                    cf = value['completion_confirmation']
                    require(fact['event_id'] == cf['event_id'] and fact['evidence'] == cf['response_evidence'],
                            'confirmation_summary_mismatch')
                if fact['kind'] == 'acceptance':
                    require(fact['evidence'] == a['evidence'], 'acceptance_summary_mismatch')
            covered.add(fact['kind'])
    require(required <= covered, 'required_summaries_missing')
    require(value.get('related_sync_uncertain') is False, 'related_sync_unknown_or_conflict')
    remote = obj(value.get('remote'), 'remote')
    require(same_target(remote.get('target'), b) and nonempty(remote.get('read_at')), 'remote_identity_not_verified')
    require(remote.get('scope_unchanged') is True, 'remote_scope_changed')
    require(remote.get('externally_reopened') is False, 'external_reopen_conflict')
    require(remote.get('state') == 'open', 'remote_already_closed_or_unknown')
    require({'close', 'state_read'} <= set(value.get('capabilities', [])), 'close_or_state_read_capability_missing')
    return {'allowed': True, 'expected_state': {'from': 'open', 'to': 'closed'}}


def recovery(value):
    """Resolve an attempted close, never infer nonexecution from current open alone."""
    value = obj(value, 'recovery')
    require(value.get('operation') == 'close' and value.get('status') in ('sending', 'unknown'), 'invalid_recovery_operation')
    require(value.get('original_request_queried') is True, 'query_original_request_first')
    require(same_target(value.get('target'), value.get('remote_target')), 'recovery_target_conflict')
    if value.get('conflict') or value.get('externally_reopened'):
        return dict(status='blocked', reason='external_or_authorization_conflict')
    if value.get('permission_denied'):
        return dict(status='blocked', reason='permission_denied')
    if value.get('remote_state') == 'closed':
        if value.get('attributable') is True and nonempty(value.get('request_receipt')) and value.get('readback_verified') is True:
            return dict(status='synced', remote_state='closed', attribution='own_request')
        return dict(status='unknown', remote_state='closed', attribution='external_or_unknown')
    if value.get('definitively_not_executed') is True and nonempty(value.get('terminal_evidence')):
        return dict(status='pending', reason='confirmed_not_executed')
    return dict(status='unknown', reason='no_terminal_execution_evidence')


def comment(value):
    """Prepare/reconcile a comment from actual paginated raw reads, no remote I/O."""
    value = obj(value, 'comment_context')
    require(value.get('status') in ('pending', 'sending', 'unknown', 'synced', 'blocked'), 'invalid_sync_status')
    require(value.get('identity_verified') is True, 'comment_target_not_verified')
    require(value.get('pages_complete') is True, 'comment_pagination_incomplete')
    require(value.get('raw_bodies_readable') is True, 'comment_raw_body_unavailable')
    require(nonempty(value.get('sync_key')) and nonempty(value.get('body_sha256')), 'comment_identity_missing')
    matches = value.get('matches')
    require(isinstance(matches, list), 'comment_matches_required')
    require(len(matches) <= 1, 'multiple_comment_matches')
    if matches:
        match = obj(matches[0], 'comment_match')
        require(match.get('sync_key') == value['sync_key'] and match.get('body_sha256') == value['body_sha256'] and
                same_target(match.get('target'), value.get('target')), 'comment_body_or_target_conflict')
        require(nonempty(match.get('receipt')) and match.get('readback_verified') is True, 'comment_readback_unverified')
        return dict(status='synced', action='none', receipt=match['receipt'])
    if value['status'] == 'synced':
        return dict(status='blocked', action='none', reason='previous_comment_missing_or_modified')
    if value['status'] in ('sending', 'unknown') and not (
            value.get('definitively_not_executed') is True and nonempty(value.get('terminal_evidence'))):
        return dict(status='unknown', action='none', reason='no_terminal_execution_evidence')
    require(value.get('authorization_valid') is True and value.get('policy_enabled') is True,
            'comment_authorization_or_policy_inactive')
    return dict(status='pending', action='persist_sending_then_send_once')


def outcome(value):
    """Classify real transport/readback observations for either operation."""
    value = obj(value, 'outcome')
    require(value.get('operation') in ('comment', 'close'), 'invalid_operation')
    result = value.get('result')
    if result in ('permission_denied', 'identity_conflict', 'missing_capability', 'body_conflict'):
        return dict(status='blocked', reason=result)
    if result == 'confirmed_not_executed':
        require(nonempty(value.get('terminal_evidence')), 'terminal_evidence_required')
        return dict(status='pending', reason=result)
    if result in ('timeout', 'interrupted', 'readback_failed', 'response_incomplete'):
        return dict(status='unknown', reason=result)
    require(result == 'verified' and value.get('same_target') is True and
            value.get('readback_verified') is True and value.get('attributable') is True and
            nonempty(value.get('receipt')), 'operation_not_verified')
    require(value['operation'] != 'close' or value.get('remote_state') == 'closed', 'close_readback_required')
    return dict(status='synced', receipt=value['receipt'])


def key(value):
    value = obj(value, 'key')
    b = target(value.get('binding'))
    require(nonempty(value.get('feature_id')) and nonempty(value.get('event_id')) and
            type(value.get('revision')) is int and value['revision'] > 0, 'invalid_event_identity')
    row = [value['feature_id'], value['revision'], value['event_id']] + [b[k] for k in TARGET_FIELDS]
    require(value.get('schema_version') in (1, 2), 'unknown_record_schema')
    require(value.get('operation') in ('comment', 'close'), 'invalid_operation')
    if value['schema_version'] == 1:
        require(value['operation'] == 'comment', 'legacy_record_comment_only')
    else:
        row.append(value['operation'])
    return {'sync_key': hashlib.sha256(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()}


def unique_object(pairs):
    result = {}
    for k, v in pairs:
        require(k not in result, 'duplicate_json_key:' + k)
        result[k] = v
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    checks = dict(config=config, target=target, authorization=authorization, release=release,
                  close=close, confirmation=confirmation, recovery=recovery, comment=comment, outcome=outcome, key=key)
    parser.add_argument('check', choices=checks)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        value = json.loads(args.input.read_text(encoding='utf-8'), object_pairs_hook=unique_object)
        print(json.dumps({'ok': True, 'result': checks[args.check](value)}, ensure_ascii=False))
        return 0
    except (ValueError, OSError, TypeError, KeyError, AttributeError) as error:
        print(json.dumps({'ok': False, 'reason': str(error)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
