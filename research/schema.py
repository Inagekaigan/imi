"""Shared label schema; unknown human categories use -1, never false negatives."""
LABELS = ['negation', 'uncertainty', 'quantity', 'agent', 'temporal', 'conditional',
          'entity_terminology', 'omission', 'addition', 'other']
TITLES = ['Negation / scope', 'Certainty / modality', 'Quantity / unit', 'Actor / recipient',
          'Time / deadline', 'Conditional meaning', 'Entity / terminology', 'Missing information',
          'Added information', 'Other semantic change']
SCHEMA_VERSION = 2
