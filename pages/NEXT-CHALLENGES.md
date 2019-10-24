# Challenges:

## Recognize and rename fields to concept references automatically, via ML.

1. Create a large number of these normalization templates for a lot of data sources.
2. Machine-learn the **field-names**, and **corresponding concepts**, so that the data gets normalized automatically, and ready for analysts.
3. Result:
    - we shall have a universal data normalizer, which given any data, is able to automatically:
        - assign proper fields and value types to it.
        - identify their position in the nested hierarchies
        - understand their ontological meaning in contexts of their positions
