# Still placeholders
- fixtures/bb_group.PLACEHOLDER.json: synthetic group payload. Finish: capture a real group message via capture_webhook.py, scrub, rename to bb_group.json, update tests.
- fixtures/CL.PLACEHOLDER.loc.vcf (and bb_location.PLACEHOLDER.json): synthetic location pin. Finish: capture a real shared-location .loc.vcf message, scrub, replace, update test_location.py.
- Uncommitted stubs (C/B own): app/models.py, app/core/handler.py, app/data/*, requirements.txt. Finish: C/B's real versions land.
- DRY_RUN=1 in the local env file. Finish: remove it (or set 0) when ready to send for real.
