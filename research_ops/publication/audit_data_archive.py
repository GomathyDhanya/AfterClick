"""Compatibility entrypoint; implementation moved to publication/analysis/."""

from research_ops.publication._compat import expose

expose("research_ops.publication.analysis.audit_data_archive", globals())
