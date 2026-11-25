SHELL := /bin/bash
SKILLTOWORKFLOW ?= $(HOME)/.local/bin/skilltoworkflow
SKILL_SURFACE ?= $(HOME)/.rig/bin/skill-surface

.PHONY: verify test hooks workflows skillopt corpus surface

# /rigstrategy blueprint done-test (blueprints/rigstrategy/ARCHITECTURE.md):
# pytest green without PYTHONPATH; 4 hooks executable; all 110 step workflows pass
# skilltoworkflow check; all 136 skills pass /skilloptimizer static+native eval;
# corpus counts good>=1000 bad>=300 (harvested & v1 calibrated); /rigstrategy
# resolves on the Aside skill surface.
verify: test hooks workflows skillopt corpus surface
	@echo "verify: all gates green"

test:
	python3 -m pytest -q

hooks:
	@for h in pre-route-redact post-route-audit pre-done-jev post-run-learn; do \
	  test -x rigstrategy/hooks/$$h.sh || { echo "MISSING/NOT-EXEC $$h.sh"; exit 1; }; \
	done; \
	echo "hooks: 4/4 executable"

workflows:
	@total=0; fail=0; \
	for f in rigstrategy/workflows/*.workflow.js; do \
	  total=$$((total+1)); \
	  $(SKILLTOWORKFLOW) check --file $$f --json >/dev/null 2>&1 \
	    || { echo "FAIL $$f"; fail=$$((fail+1)); }; \
	done; \
	echo "workflows: $$((total-fail))/$$total pass skilltoworkflow check"; \
	test $$total -eq 110 -a $$fail -eq 0

skillopt:
	python3 rigstrategy/meta_harness.py

corpus:
	python3 rigstrategy/check_corpus.py

surface:
	@$(SKILL_SURFACE) where rigstrategy >/dev/null && echo "surface: /rigstrategy resolves"
