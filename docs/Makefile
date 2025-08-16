# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD  ?= sphinx-build
SOURCEDIR    = .
BUILDDIR     = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Build HTML documentation
html:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

# Clean build artifacts
clean:
	@rm -rf "$(BUILDDIR)"
	@echo "Build artifacts cleaned."

# Live reload server for development
livehtml:
	sphinx-autobuild -b html $(SPHINXOPTS) "$(SOURCEDIR)" "$(BUILDDIR)/html"

# Serve documentation locally
serve: html
	@echo "Serving documentation at http://localhost:8000"
	@cd $(BUILDDIR)/html && python -m http.server 8000

# Build and open in browser
open: html
	@echo "Opening documentation in browser..."
	@open $(BUILDDIR)/html/index.html || xdg-open $(BUILDDIR)/html/index.html

# Auto-generate API documentation
apidoc:
	sphinx-apidoc -o . ../src/hwautomation --force --separate
	@echo "API documentation generated."

# Full rebuild (clean + html)
rebuild: clean html

# Check for broken links
linkcheck:
	@$(SPHINXBUILD) -b linkcheck "$(SOURCEDIR)" "$(BUILDDIR)/linkcheck" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
