2026-05-15T23:23:49.369624875Z ==> Setting WEB_CONCURRENCY=1 by default, based on available CPUs in the instance
2026-05-15T23:24:01.094594619Z ==> Running 'uvicorn main:app --host 0.0.0.0 --port $PORT'
2026-05-15T23:24:15.877504756Z Traceback (most recent call last):
2026-05-15T23:24:15.879281773Z   File "/opt/render/project/src/.venv/bin/uvicorn", line 7, in <module>
2026-05-15T23:24:15.879296063Z     sys.exit(main())
2026-05-15T23:24:15.879301043Z              ~~~~^^
2026-05-15T23:24:15.879306363Z   File "/opt/render/project/src/.venv/lib/python3.14/site-packages/click/core.py", line 1514, in __call__
2026-05-15T23:24:15.879315213Z     return self.main(*args, **kwargs)
2026-05-15T23:24:15.879319894Z            ~~~~~~~~~^^^^^^^^^^^^^^^^^
2026-05-15T23:24:15.879324674Z   File "/opt/render/project/src/.venv/lib/python3.14/site-packages/click/core.py", line 1435, in main
2026-05-15T23:24:15.879329894Z     rv = self.invoke(ctx)
2026-05-15T23:24:15.879334514Z   File "/opt/render/project/src/.venv/lib/python3.14/site-packages/click/core.py", line 1298, in invoke
2026-05-15T23:24:15.879339514Z     return ctx.invoke(self.callback, **ctx.params)
2026-05-15T23:24:15.879344554Z            ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-05-15T23:24:15.879349074Z   File "/opt/render/project/src/.venv/lib/python3.14/site-packages/click/core.py", line 853, in invoke
2026-05-15T23:24:15.879353594Z     return callback(*args, **kwargs)
2026-05-15T23:24:15.879358234Z   File "/opt/render/project/src/.venv/lib/python3.14/site-packages/uvicorn/main.py", line 441, in main
2026-05-15T23:24:15.879362824Z     run(
2026-05-15T23:24:15.879367334Z     ~~~^
2026-05-15T23:24:15.879371664Z         app,
2026-05-15T23:24:15.879376544Z         ^^^^
2026-05-15T23:24:15.879381064Z     ...<48 lines>...
2026-05-15T23:24:15.879385814Z         reset_contextvars=reset_contextvars,
2026-05-15T23:24:15.879390475Z         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-05-15T23:24:15.879394815Z     )
2026-05-15T23:24:15.879399225Z     ^
2026-05-15T23:24:15.879403905Z   File "/opt/render/project/src/.venv/lib/python3.14/site-packages/uvicorn/main.py", line 609, in run
2026-05-15T23:24:15.879408395Z     config.load_app()
2026-05-15T23:24:15.879412835Z     ~~~~~~~~~~~~~~~^^
2026-05-15T23:24:15.879417125Z   File "/opt/render/project/src/.venv/lib/python3.14/site-packages/uvicorn/config.py", line 415, in load_app
2026-05-15T23:24:15.879422525Z     return import_from_string(self.app)
2026-05-15T23:24:15.879429485Z   File "/opt/render/project/src/.venv/lib/python3.14/site-packages/uvicorn/importer.py", line 19, in import_from_string
2026-05-15T23:24:15.879434395Z     module = importlib.import_module(module_str)
2026-05-15T23:24:15.879439115Z   File "/opt/render/project/python/Python-3.14.3/lib/python3.14/importlib/__init__.py", line 88, in import_module
2026-05-15T23:24:15.879443415Z     return _bootstrap._gcd_import(name[level:], package, level)
2026-05-15T23:24:15.879448155Z            ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-05-15T23:24:15.879452736Z   File "<frozen importlib._bootstrap>", line 1398, in _gcd_import
2026-05-15T23:24:15.879457065Z   File "<frozen importlib._bootstrap>", line 1371, in _find_and_load
2026-05-15T23:24:15.879474226Z   File "<frozen importlib._bootstrap>", line 1342, in _find_and_load_unlocked
2026-05-15T23:24:15.879479896Z   File "<frozen importlib._bootstrap>", line 938, in _load_unlocked
2026-05-15T23:24:15.879484456Z   File "<frozen importlib._bootstrap_external>", line 759, in exec_module
2026-05-15T23:24:15.879488756Z   File "<frozen importlib._bootstrap>", line 491, in _call_with_frames_removed
2026-05-15T23:24:15.879493216Z   File "/opt/render/project/src/backend/main.py", line 16, in <module>
2026-05-15T23:24:15.879497836Z     from routers.web_router import router as web_router
2026-05-15T23:24:15.879515276Z   File "/opt/render/project/src/backend/routers/web_router.py", line 1105, in <module>
2026-05-15T23:24:15.879518696Z     def panel_cluster(request: Request, current_user: dict = Depends(verify_token_cookie)):
2026-05-15T23:24:15.879521617Z                                                              ^^^^^^^
2026-05-15T23:24:15.879534237Z NameError: name 'Depends' is not defined
2026-05-15T23:24:17.643886103Z ==> Exited with status 1
2026-05-15T23:24:17.646285498Z ==> Common ways to troubleshoot your deploy: https://render.com/docs/troubleshooting-deploys
