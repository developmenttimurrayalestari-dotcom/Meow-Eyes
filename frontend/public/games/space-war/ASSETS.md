# Source PNG Meow Space War

Mode pembuatan: **builtin imagegen**, 11 November 2026. Identitas pilot mengacu pada logo asli `frontend/public/logo-meow.jpg`: kucing putih, telinga dan hidung oranye, lidah, dan kacamata hitam. Source PNG ini langsung dipakai oleh engine; tidak memerlukan hasil potong terpisah.

| Source | Ukuran | Isi |
| --- | --- | --- |
| [meow-pilot.png](meow-pilot.png) | 1774 × 887, RGBA | Maskot di kokpit pesawat menghadap kanan |
| [aliens-explosions.png](aliens-explosions.png) | 1536 × 1024, RGBA | Atlas 3 × 2: tiga alien, tiga frame ledakan |
| [ui-laser.png](ui-laser.png) | 1536 × 1024, RGBA | Atlas 3 × 2: hati, atas, bawah, laser, bintang poin, impact |
| [galaxy.png](galaxy.png) | 2172 × 724, RGB | Latar galaksi biru; sengaja opak |

Ketiga sprite PNG memiliki kanal alpha asli (piksel sudut alpha 0). Atlas memakai petak 512 × 512, urutan kiri ke kanan lalu atas ke bawah. `manifest.json` menjelaskan koordinat dan urutan animasi. Engine merender teks poin secara dinamis di atas latar agar terbaca pada mobile. Latar digulung dengan tile berselang cermin dan lapisan bintang terpisah untuk parallax.

## Prompt final

### Pilot (referensi: logo Meow Eyes, background transparan)

Use case: stylized-concept. Asset type: transparent PNG sprite for a 2D side-scrolling ecommerce mini-game, Meow Space War. Reference image: the supplied Meow Eyes logo defines mascot identity. Preserve its white cat, orange inner ears and nose, playful expression with orange tongue, oversized shiny black sunglasses, thick charcoal outline. Adapt this same mascot into the visible clear cockpit of a compact futuristic teal/orange spaceship, facing RIGHT, side view with slight three-quarter cockpit visibility. Whole ship fully visible, orange rocket flame trailing left, cute polished flat cartoon game art, bold clean contours, no lettering or logo text, generous transparent padding, genuine transparent background. One centered isolated sprite, wide aspect composition. Do not include an orange circular backdrop.

### Alien dan animasi ledakan (background transparan)

Use case: stylized-concept. Asset type: PNG sprite atlas on genuine transparent background for Meow Space War, cute polished 2D side-scrolling shooter. A precisely arranged 3 columns by 2 rows grid of SIX clearly separated, fully contained sprites with equal large transparent cell padding, no borders, no lettering, no text. Top row: three different enemy alien spacecraft all facing LEFT: purple squid UFO, lime green alien saucer, coral armored alien drone. Bottom row: three consecutive explosion animation frames centered in each cell, small orange initial burst, expanding yellow-orange starburst, fading orange sparks. Match bold charcoal outlines and cheerful flat cartoon style, teal/orange/purple space arcade palette. All objects separated on alpha transparency with no background.

### UI dan proyektil (background transparan)

Use case: stylized-concept. Asset type: transparent PNG game UI atlas for Meow Space War. Precisely arranged 3 columns by 2 rows grid with SIX isolated graphic sprites, each fully inside its equal cell with generous transparent padding. Top row: bright red heart health icon; futuristic cyan neon circular UP ARROW control; matching futuristic cyan neon circular DOWN ARROW control. Bottom row: glowing cyan laser projectile facing right; orange gold star token for score; electric blue impact flash. Polished cute 2D cartoon space arcade style, bold clean silhouettes, genuine transparent background. No written text, no border grid, no decorative backdrop.

### Galaksi (background opak)

Use case: stylized-concept. Asset type: horizontal seamless looping 2D game background PNG for Meow Space War side-scrolling shooter. Wide blue and indigo outer-space galaxy, sparse tiny distant stars with subtle cyan/violet nebula wisps, depth and quiet empty central playing area, polished cartoon painted game art. Tile seamlessly from LEFT edge to RIGHT edge for repeated horizontal scrolling. No planets cut by borders, no ships, no characters, no UI, no text. Dark enough for bright teal/orange sprites to stand out. Opaque deep blue background.
