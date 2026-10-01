# Milestone 1: Read the data and run the starter

Listing fields: `id`, `title`, `description`, `category`, `style_tags`, `size`,
`condition`, `price`, `colors`, `brand`, `platform`.

Read records `lst_001` through `lst_006`: Levi's jeans ($38), butterfly baby tee
($18), flannel shirt ($22), track jacket ($45), corduroy pants ($32), and bootleg
style graphic tee ($24). The baby tee and bootleg tee have both `vintage` and
`graphic tee` tags and cost less than $30.

Filtering details: `price` is numeric; `style_tags` and `colors` are lists;
`brand` may be null. Sizes are strings such as `S/M`, `XL (oversized)`, and
`W30 L30`, so exact size matching needs care. Three fields to remember:
`price`, `size`, and `style_tags`.

A wardrobe is an object containing an `items` list. Each item has `id`, `name`,
`category`, `colors`, `style_tags`, and optional `notes` (which can be null).
An empty wardrobe has `items: []`; the schema's example also includes a `_note`.
There are 40 listings and 10 example wardrobe items.

Successfully ran:

```bash
source .venv/bin/activate
python app.py fields
python app.py listings --full -n 6
python app.py examples
python app.py ask 'vintage graphic tee under $30'
```

The starter query returned the expected message:

> The planning loop isn't built yet — see the TODO in agent.py.

It made zero model calls. The starter is at the expected Milestone 1 position.
