# Project rules
Use the existing flat Python module structure. Shipping rules belong in shipping.py and checkout.py consumes that function. Reuse the call chain. No new package layers, repositories or DI framework. Use stdlib checks for this isolated fixture.
