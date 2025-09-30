import src.data.languages.romanian_standard as ro_std
from src.domain.layout_phenotype import LayoutPhenotype
ro_config = ro_std.get_layout()

# Create layout and apply the configuration
layout = LayoutPhenotype()
layout.apply_language_layout(ro_config)
print(layout)
