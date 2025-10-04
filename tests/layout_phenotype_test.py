import src.data.languages.romanian_standard as ro_std
from src.core.layout_phenotype import LayoutPhenotype
ro_config = ro_std.get_layout()

# Create layout and apply the configuration
layout = LayoutPhenotype()
# layout.apply_language_layout(ro_config)
layout.debug_print_layout()
