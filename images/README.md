# Site images

Drop image files here and reference them from `index.html`.

## Raffle prize photos

Add the file, then uncomment and correct the matching line in the
`PRIZE_IMAGES` block in `index.html`. Keys map to the prize rows:

| Key      | Prize                                          |
| -------- | ---------------------------------------------- |
| `cooler` | Pendleton Whisky Taiga Cooler                   |
| `bottle` | Pendleton Whisky Champions Edition Bottle       |
| `buckle` | Montana Silversmiths 20th Anniversary Buckle    |
| `purse`  | Portland Leather Purse                          |
| `hat`    | Pendleton Hat Co. gift certificates             |

Thumbnails render at 62x62 (48x48 on phones), cropped to a square, so
roughly square source images look best. Anything from about 200px up is
plenty. Keys left commented out simply show no thumbnail.

## Store products

Store items are listed in the `TETWP_PRODUCTS` array in `index.html`.
Each entry takes a `name`, `price`, `url`, and an optional `img` that can
point at a file in this folder.
