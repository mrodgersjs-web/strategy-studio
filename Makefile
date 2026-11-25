SHELL := /bin/bash
SKILLTOWORKFLOW ?= $(HOME)/.local/bin/skilltoworkflow
SKILL_SURFACE ?= $(HOME)/.rig/bin/skill-surface

.PHONY: verify test workflows corpus surface

# /rigstrategy blueprint done-test (blueprints/rigstrategy/ARCHITECTURE.md):
# pytest green without PYTHONPATH; all 110 step workflows pass skilltoworkflow
# check; corpus counts good>=1000 bad>=300; /rigstrategy resolves on the Aside
# skill surface. The Jev done.claim gate runs at delivery, not in this target.
verify: test workflows corpus surface
	@echo "verify: all gates green"

test:
	python3 -m pytest -q

workflows:
	@total=0; fail=0; \
	for f in rigstrategy/workflows/*.workflow.js; do \
	  total=$$((total+1)); \
	  $(SKILLTOWORKFLOW) check --file $$f --json >/dev/null 2>&1 \
	    || { echo "FAIL $$f"; fail=$$((fail+1)); }; \
	done; \
	echo "workflows: $$((total-fail))/$$total pass skilltoworkflow check"; \
	test $$total -eq 110 -a $$fail -eq 0

corpus:
	python3 rigstrategy/check_corpus.py

surface:
	@$(SKILL_SURFACE) where rigstrategy >/dev/null && echo "surface: /rigstrategy resolves"
