# POD gift playbook

Working notes for researching and designing personalized print-on-demand gifts for US buyers. This file is guidance for how to work. It is not evidence: every claim in a campaign report must cite a source you read during that campaign.

## How successful sellers work

- **Buyer first, product second.** Winning listings address an identity or relationship (dog mom, night-shift nurse, new grandparent, long-distance best friend), then choose the product. Name the buyer and the recipient before choosing a style.
- **Personalization is the product.** Common forms: a name, a date, a role, a family or pet count, initials, a place, an uploaded photo turned into art. One clear personalization reads better at product size than several.
- **Stack niches carefully.** Combining two identities (nurse + dog owner) narrows competition. Check that the combination still has buyers.
- **Trends saturate quickly.** A theme that many stores copy loses its edge within weeks. Prefer a fresh treatment of a proven theme over a copy of a current hit.
- **Gift products.** Mugs, tumblers, ornaments, blankets, canvases, doormats, sweatshirts and tees carry most personalized gift sales.

## Seasonal planning

- Buying peaks roughly four to six weeks before an occasion. Listings should be live six to eight weeks before it, earlier for Christmas.
- For the winter holidays sellers prepare niches, samples and mockups in late summer, publish listings by early October and run ads from mid October to late November. New launches in the first half of December rarely arrive in time.
- Order cutoffs depend on production plus carrier time. Print providers usually announce theirs by mid October. Treat the helper's `order_cutoff_estimate` as a planning heuristic and tell the customer to confirm with their provider.
- `research.py calendar` lists upcoming occasions with their windows: `plan`, `launch_now`, `in_market`, `last_call`.

## Reading the market

| Source | What is publicly readable | Limits |
| --- | --- | --- |
| Amazon category Best Sellers and New Releases | Ranked items with title and rating | Rank changes hourly; the top-level page may show an interstitial; do not bypass it |
| Etsy | Trend reports and news; search pages refuse automated reads | Badge rules are unpublished; an official API exists but needs the customer's own key |
| Shopify storefronts | `research.py storefront` reads the public catalog feed: titles, types, tags, publish dates. Cite the store pages it returns, not the feed | No sales or stock counts; sorted collection URLs are disallowed by robots.txt and are not read |
| TikTok Creative Center | Little without login; pages render in the browser only | Use TikTok's own guidance and current coverage |
| Google Trends, Pinterest Trends | Refuse automated reads | Use published reports that quote them |
| Meta Ad Library | Renders in a browser only | No spend or impression data |

Storefronts that sell personalized gifts to US buyers and publish a catalog feed include wanderprints.com, macorner.co, pawfecthouse.com, pawsionate.com, trendingcustom.com, personalhouse.com, crownandpaw.com, westandwillow.com, unifury.com and famvibe.com. Choose the ones that match the campaign's buyer, and look for others through search.

Sources worth reading for seasonal demand: National Retail Federation holiday and occasion surveys (nrf.com), Pinterest Predicts, Etsy trend reports, and the Printful, Printify, Gelato and Shopify blogs.

## What a winning-design signal can and cannot tell you

| Signal | Suggests | Cannot tell you |
| --- | --- | --- |
| Marketplace rank or badge | Current demand for that listing | Units sold; why it sells |
| Review count and recent reviews | Sustained sales over time | Exact volume; review rates vary by category |
| Position in a store's best-seller collection | What the merchant promotes | Sales; collections can be curated by hand |
| Newly published products | What competitors are betting on now | Whether the bet pays off |
| Many near-identical listings | A validated theme | It also means saturation and possible IP risk |
| An ad running for many weeks | The advertiser keeps paying for it | Spend or profit |
| Video views | Attention | Purchases |

Report the signal and its limit together.

## Design practice

- Text must survive product size: large, high-contrast lettering; at most two typefaces.
- Keep the artwork inside a safe area and away from edges, handles and seams.
- Print files: sRGB, PNG for artwork with transparency, about 300 DPI at print size for small detailed products and 150 DPI as a floor for large ones. A generated image is a concept; print readiness needs the provider's template and a preflight.
- Offer colourways or styles that differ at a glance so the buyer can choose.
- Original work only. No brand names, characters, celebrity likenesses, sports teams or lyrics.

## Mockup practice

- A lifestyle setting that matches the buyer, with the print facing the camera and fully readable.
- Show a finished personalization example, not a placeholder.
- Neutral, uncluttered surroundings; natural light.

## Short-video practice

- Vertical 9:16, at least 720p. In a 5-second video the product and print are visible from the first frame.
- One simple move: a slow push-in, a gentle turn or a hand placing the product.
- Sound on. Describe the sound in the prompt. Avoid voice-over and any claim, price, delivery promise or review.
- An AI-made demonstration must not pretend to be a customer's testimonial.
