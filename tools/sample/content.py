"""Content of the bundled sample campaign.

Research sources are real pages, read on 2026-09-30: Amazon pages in a browser, competitor stores through their
public catalogs, the rest as web pages or search results. Reviewer comments, scores and rationales are written
examples. Media are stand-ins, partly taken from an earlier real run (see media/README.md).
"""

BRIEF = {
    "name": "Botanical name mug · best-friend gift",
    "product": "Mug",
    "platform": "TikTok",
    "audience": "",
    "brief": ("Create an original personalized ceramic mug as a Christmas gift for a close friend. Target buyers are women aged 25-44 in the "
              "United States who love plants and calm, modern homes. The print shows the exact name ALEX with a botanical motif in blue. "
              "Deliver isolated flat print artwork on a plain white canvas, a lifestyle mockup with the print facing the camera, and a "
              "5-second vertical product video with soft background sound. Keep the artwork and the ALEX lettering readable and consistent "
              "across all assets. No extra text, trademarks, invented claims or customer testimonials."),
    "store": "macorner.co",
}
LIMITS = {"max_rounds": 2, "target_score": 4.5, "watermark": False, "generate_audio": True, "language": "vi", "design_count": 5, "select_max": 3}
SELECTION = ["v1", "v3", "v2"]

INSIGHTS = {
    "market": "Hoa Kỳ",
    "audience": "Phụ nữ 25–44 tuổi, yêu cây cỏ và không gian sống hiện đại, nhẹ nhàng",
    "occasion": "Giáng sinh 2026",
    "recipient": "Bạn thân",
    "tone": "Ấm áp, tinh tế, tối giản",
    "personalization": "Tên riêng in chính xác: ALEX",
}

AMAZON = "https://www.amazon.com/"
SOURCES = [
    {"id": "s1", "channel": "amazon", "access": "fetched", "title": "Amazon Best Sellers: Best Novelty Coffee Mugs",
     "url": AMAZON + "Best-Sellers-Novelty-Coffee-Mugs/zgbs/kitchen/9302388011",
     "finding": "Trong top 30 cốc bán chạy ngày 30/09/2026: cốc quà tặng bạn thân của Biching đứng #8 (4,8 sao, 4.519 đánh giá); "
                "hai cốc chữ lồng (monogram) kèm hộp quà của Collective Home ở #21 và #23; bốn cốc in tên hoặc ảnh theo yêu cầu (#15, #20, #29). "
                "Nhiều cốc bán chạy được đặt tên theo người nhận: bạn thân, đồng nghiệp, giáo viên.",
     "metric": {"label": "Thứ hạng cốc quà tặng bạn thân", "value": "#8 trong Novelty Coffee Mugs"}},
    {"id": "s2", "channel": "amazon", "access": "fetched", "title": "Personalized Name & Birth Flower Coffee Mug – True Passion Styles",
     "url": AMAZON + "Personalized-Name-Birth-Flower-Coffee/dp/B0GV8TRRQ5",
     "finding": "Cốc “hoa tháng sinh + tên” nhắm đúng người nhận là bạn thân (“Best Friend, Bestie”) nhưng mới xếp #8.671 trong Novelty Coffee Mugs: "
                "chủ đề hoa kèm tên đã có người bán, nhưng chưa có mẫu nào dẫn đầu.",
     "metric": {"label": "Best Sellers Rank", "value": "#8.671 trong Novelty Coffee Mugs"}},
    {"id": "s3", "channel": "amazon", "access": "fetched", "title": "Personalized Birth Flower Mug with Name & Text – Lara Laser Works",
     "url": AMAZON + "Personalized-Flower-Colors-Custom-Sister/dp/B0C2Q4DHYD",
     "finding": "Cốc hoa tháng sinh kèm tên với 11 màu tuỳ chọn, 4,6 sao từ 51 đánh giá; tiêu đề nhắm tới mẹ, chị em và phụ nữ nói chung.",
     "metric": {"label": "Đánh giá", "value": "4,6 sao · 51 lượt"}},
    {"id": "s4", "channel": "etsy", "access": "search_result", "title": "Personalized Floral Best Friends Mug, Birth Month Flowers Friendship Besties Name Coffee Mug – Etsy",
     "url": "https://www.etsy.com/listing/1821494384/personalized-floral-best-friends-mug",
     "finding": "Kết quả tìm kiếm cho thấy trên Etsy có cốc hoa tháng sinh kèm tên dành riêng cho bạn thân, chữ tên viết tay đặt cạnh bó hoa. "
                "Etsy chặn đọc tự động nên chưa xem được số đánh giá."},
    {"id": "s5", "channel": "competitor_store", "access": "helper", "title": "Wander Prints – catalog sản phẩm",
     "url": "https://wanderprints.com/collections/all",
     "finding": "Cả 60 sản phẩm mới nhất đều cá nhân hoá; “photo” xuất hiện 22 lần và “christmas” 21 lần trong tiêu đề. Phong cách nét vẽ (line art) "
                "có trong sản phẩm mới: “Custom Photo Line Art Family Portrait” và áo len “Knit Line Art”. Ngày 29/09/2026 cửa hàng đăng quà tình bạn cho nữ."},
    {"id": "s6", "channel": "competitor_store", "access": "helper", "title": "Pawfect House – catalog và bộ sưu tập Best Sellers",
     "url": "https://pawfecthouse.com/collections/best-sellers",
     "finding": "Bộ sưu tập best-seller có bình hoa “A Garden Grown From Her Heart” tặng mẹ và bà: chủ đề vườn hoa gắn với người nhận là phụ nữ. "
                "Trong 60 tiêu đề mới nhất, “birthday” xuất hiện 51 lần và “christmas” 41 lần; ngày 29/09/2026 có đĩa trang sức tặng “Besties”."},
    {"id": "s7", "channel": "competitor_store", "access": "helper", "title": "Trending Custom – catalog sản phẩm",
     "url": "https://trendingcustom.com/collections/all",
     "finding": "Mùa Giáng sinh đã bắt đầu: “christmas” xuất hiện 61 lần trong 60 tiêu đề mới nhất, phần lớn là ornament đăng ngày 28–29/09/2026. "
                "Thẻ “besties” gắn trên 5 sản phẩm; best-seller nổi bật là đèn cầu pha lê in ngày đặc biệt."},
    {"id": "s8", "channel": "competitor_store", "access": "helper", "title": "West & Willow – bộ sưu tập Best Sellers",
     "url": "https://westandwillow.com/collections/best-sellers",
     "finding": "Cốc “Custom Pet Portrait Mug” nằm trong bộ sưu tập best-seller cạnh tranh chân dung thú cưng: cốc là sản phẩm phụ bán tốt khi đi kèm một chủ đề cá nhân rõ ràng."},
    {"id": "s9", "channel": "tiktok", "access": "fetched", "title": "Creative best practices for performance ads – TikTok Business Help Center",
     "url": "https://ads.tiktok.com/help/article/creative-best-practices",
     "finding": "TikTok khuyến nghị video dọc 9:16, độ phân giải tối thiểu 720p, có âm thanh hoặc nhạc; nêu thông điệp chính trong 3 giây đầu và đặt điểm thu hút trong 6 giây đầu.",
     "metric": {"label": "Thời điểm nêu thông điệp chính", "value": "3 giây đầu"}},
    {"id": "s10", "channel": "trends", "access": "fetched", "title": "Consumers to Spend Second-Highest Amount on Record, According to NRF Holiday Survey (16/10/2025)",
     "url": "https://nrf.com/media-center/press-releases/consumers-to-spend-second-highest-amount-on-record-according-to-nrf-holiday-survey",
     "finding": "Khảo sát mùa lễ 2025 của NRF (8.247 người, 1–7/10/2025): 42% người mua sắm bắt đầu tìm và mua quà trước tháng 11. Đây là số liệu mùa 2025; chưa tìm thấy dự báo mùa 2026.",
     "metric": {"label": "Bắt đầu mua quà trước tháng 11", "value": "42%"}},
    {"id": "s11", "channel": "trends", "access": "fetched", "title": "Printify holiday guide 2026",
     "url": "https://printify.com/blog/holiday-guide/",
     "finding": "Printify khuyên chuẩn bị tài liệu marketing trước tháng 11 và cho biết hạn chót đặt hàng dịp lễ thường được công bố vào giữa tháng 10. Cốc, đồ trang trí treo cây và chăn nằm trong nhóm quà dịp lễ được liệt kê."},
    {"id": "s12", "channel": "industry", "access": "fetched", "title": "25 Best Print-on-Demand Products to Sell in 2026 – Shopify (cập nhật 08/05/2026)",
     "url": "https://www.shopify.com/blog/print-on-demand-products",
     "finding": "Shopify mô tả cốc là món quà quen thuộc với nhu cầu tăng mạnh vào quý 4; thiết kế giới hạn hoặc chất liệu cao cấp giúp sản phẩm nổi bật."},
    {"id": "s13", "channel": "industry", "access": "fetched", "title": "How to prepare perfect print files for print-on-demand – Printful (28/07/2025)",
     "url": "https://www.printful.com/blog/everything-you-need-to-know-to-prepare-the-perfect-printfile",
     "finding": "Printful khuyến nghị 300 DPI cho sản phẩm nhỏ nhiều chi tiết như cốc, hệ màu sRGB và tệp PNG hoặc JPEG.",
     "metric": {"label": "Độ phân giải tệp in cho cốc", "value": "300 DPI"}},
    {"id": "s14", "channel": "industry", "access": "fetched", "title": "Print-on-demand niches: 15 ideas for 2026 – Printify",
     "url": "https://printify.com/blog/print-on-demand-niches/",
     "finding": "Printify nhấn mạnh chọn ngách theo người mua: “A niche is who you sell it to and why they care.” Người mua muốn thấy tên, ngày tháng, thú cưng hoặc vai trò của mình trong thiết kế."},
]
for source in SOURCES:
    source["retrieved"] = "2026-09-30"

RESEARCH = {
    "summary": ("Mùa quà Giáng sinh đã bắt đầu: còn 86 ngày và cả bốn cửa hàng đối thủ được khảo sát đang đăng sản phẩm mới theo chủ đề Giáng sinh "
                "(Trending Custom dùng từ “christmas” 61 lần trong 60 tiêu đề mới). Quà cho bạn thân là một ngách rõ ràng: cốc quà tặng bạn thân đứng #8 "
                "trong top cốc bán chạy trên Amazon với 4.519 đánh giá, và cốc “hoa tháng sinh + tên” cho bạn thân đã xuất hiện trên Amazon và Etsy nhưng "
                "chưa có mẫu nào dẫn đầu. Đối thủ trên Shopify chủ yếu bán sản phẩm in ảnh, nên một thiết kế chỉ có tên và hoạ tiết thực vật sẽ khác biệt; "
                "cốc chữ lồng kèm hộp quà trong top 30 Amazon cho thấy phong cách tối giản, sang trọng cũng bán tốt."),
    "status": "complete",
    "sources": SOURCES,
    "coverage": [
        {"channel": "amazon", "status": "covered", "note": "Đọc bảng xếp hạng cốc bán chạy và hai trang sản phẩm qua trình duyệt."},
        {"channel": "etsy", "status": "limited", "note": "Etsy chặn đọc tự động; chỉ có kết quả tìm kiếm."},
        {"channel": "competitor_store", "status": "covered", "note": "Đọc catalog công khai của 4 cửa hàng đối thủ; không tính cửa hàng của khách hàng."},
        {"channel": "tiktok", "status": "limited", "note": "Có hướng dẫn chính thức của TikTok; dữ liệu video cần đăng nhập."},
        {"channel": "trends", "status": "covered", "note": "Lịch dịp lễ của hệ thống, khảo sát NRF và hướng dẫn mùa lễ của Printify."},
    ],
    "competitor_designs": [
        {"brand": "Biching (Amazon)", "product": "Best Friend Birthday Gifts for Women, Friendship Gifts – Ceramic Mug",
         "url": AMAZON + "Best-Friend-Birthday-Gifts-Friendship/dp/B085VYLRFQ",
         "style_tags": ["Quà bạn thân", "Câu chữ tình bạn", "Tặng nữ"], "signal": "#8 Best Sellers · 4.519 đánh giá",
         "why_it_works": "Tiêu đề gọi đúng người nhận (bạn thân, bestie, BFF) và dịp tặng, nên bán quanh năm chứ không chỉ mùa lễ. Không cá nhân hoá tên: đây là khoảng trống cho cốc in tên.", "source_ids": ["s1"]},
        {"brand": "Collective Home (Amazon)", "product": "Ceramic Coffee Mug, 15 oz Monogram Cup with Gift Box",
         "url": AMAZON + "COLLECTIVE-HOME-Monogram-Personalized-Luxurious/dp/B0BZY59D7B",
         "style_tags": ["Chữ lồng", "Hộp quà", "Sang trọng"], "signal": "#21 Best Sellers · 899 đánh giá",
         "why_it_works": "Chỉ một chữ cái đầu mạ vàng, rất tối giản, bán kèm hộp quà: người mua trả tiền cho cảm giác quà tặng cao cấp.", "source_ids": ["s1"]},
        {"brand": "True Passion Styles (Amazon)", "product": "Personalized Name & Birth Flower Coffee Mug",
         "url": AMAZON + "Personalized-Name-Birth-Flower-Coffee/dp/B0GV8TRRQ5",
         "style_tags": ["Hoa tháng sinh", "Tên riêng", "Bạn thân"], "signal": "#8.671 Best Sellers",
         "why_it_works": "Kết hợp hoa và tên đúng như brief, nhưng xếp hạng thấp: chủ đề có nhu cầu nhưng chưa có thiết kế nổi bật, là cơ hội để làm tốt hơn.", "source_ids": ["s2"]},
        {"brand": "Etsy", "product": "Personalized Floral Best Friends Mug, Birth Month Flowers",
         "url": "https://www.etsy.com/listing/1821494384/personalized-floral-best-friends-mug",
         "style_tags": ["Hoa tháng sinh", "Chữ viết tay", "Bạn thân"], "signal": "Kết quả tìm kiếm",
         "why_it_works": "Bó hoa kèm tên viết tay dành riêng cho bạn thân; cho thấy người bán thủ công trên Etsy đã khai thác ngách này.", "source_ids": ["s4"]},
        {"brand": "Pawfect House", "product": "Custom Flower Vase With Ribbon – A Garden Grown From Her Heart",
         "url": "https://pawfecthouse.com/products/custom-flower-vase-with-ribbon-personalized-mothers-day-birthday-gifts-for-mom-grandma-a-garden-grown-from-her-heart",
         "style_tags": ["Vườn hoa", "Tặng phụ nữ", "Cá nhân hoá"], "signal": "Trong bộ sưu tập Best Sellers",
         "why_it_works": "Chủ đề vườn hoa gắn với người nhận là phụ nữ được cửa hàng xếp vào nhóm bán chạy; hoạ tiết thực vật hợp với nhóm khách này.", "source_ids": ["s6"]},
        {"brand": "Wander Prints", "product": "Friendship Gift For Woman, Best Friend, Bestie, BFF – Stained Glass Christmas Tree",
         "url": "https://wanderprints.com/products/friendship-gift-for-woman-best-friend-bestie-bff-personalized-custom-photo-semi-realistic-portrait-it-takes-a-long-time-stained-glass-christmas-tree-hn037hal4249",
         "style_tags": ["Quà tình bạn", "Chân dung từ ảnh", "Giáng sinh"], "signal": "Mới đăng 29/09/2026",
         "why_it_works": "Nhắm thẳng vào nữ tặng bạn thân dịp Giáng sinh nhưng dùng ảnh cá nhân; thiết kế chỉ có tên sẽ dễ đặt mua và khác biệt.", "source_ids": ["s5"]},
    ],
    "seasonal_focus": [
        {"occasion": "Giáng sinh (25/12/2026)", "calendar_id": "christmas", "why": "Dịp tặng quà chính của brief; đối thủ đã đăng sản phẩm Giáng sinh từ cuối tháng 9. Theo lịch nên đăng bán trước 30/10; hạn đặt hàng ước tính 11/12 cần xác nhận lại với nhà in.", "source_ids": ["s11", "s7"]},
        {"occasion": "Black Friday – Cyber Monday (27–30/11/2026)", "calendar_id": "black_friday", "why": "42% người mua bắt đầu mua quà trước tháng 11; tài liệu quảng cáo cần sẵn sàng trước tháng 11.", "source_ids": ["s11", "s10"]},
        {"occasion": "Galentine's Day (13/02/2027)", "calendar_id": "galentines", "why": "Dịp tặng quà cho bạn thân nữ ngay sau mùa lễ; có thể dùng lại thiết kế tên riêng.", "source_ids": [], "basis": "hypothesis"},
    ],
    "keywords": [
        {"term": "best friend / bestie / BFF", "note": "Có trong tiêu đề cốc #8 trên Amazon và quà tình bạn mới của Wander Prints.", "source_ids": ["s1", "s5"]},
        {"term": "birth flower", "note": "Cốc hoa tháng sinh kèm tên trên Amazon và Etsy.", "source_ids": ["s2", "s3", "s4"]},
        {"term": "monogram", "note": "Hai cốc chữ lồng kèm hộp quà trong top 30 Amazon.", "source_ids": ["s1"]},
        {"term": "line art", "note": "Có trong tiêu đề sản phẩm mới của Wander Prints.", "source_ids": ["s5"]},
        {"term": "christmas", "note": "21–61 lần trong 60 tiêu đề mới của mỗi cửa hàng đối thủ.", "source_ids": ["s5", "s6", "s7"]},
    ],
    "opportunities": [
        {"title": "Nét lá mảnh, tên làm trung tâm", "insight": "Đối thủ trên Shopify chủ yếu in ảnh; nét vẽ (line art) đang xuất hiện trong sản phẩm mới, và chủ đề hoa lá bán tốt với khách nữ.",
         "design_direction": "Nét vẽ mảnh màu xanh dương, chữ serif lớn, nhiều khoảng trắng", "source_ids": ["s5", "s6"]},
        {"title": "Hoa lá mềm mại quanh tên", "insight": "Cốc hoa kèm tên cho bạn thân đã có trên Amazon và Etsy nhưng chưa có mẫu dẫn đầu.",
         "design_direction": "Vòng lá màu nước ôm quanh tên", "source_ids": ["s2", "s4"]},
        {"title": "Chữ lớn, đọc được trong video", "insight": "TikTok khuyên nêu thông điệp trong 3 giây đầu, nên tên phải đọc được ngay trên video dọc.",
         "design_direction": "Chữ in hoa cỡ lớn, tương phản cao", "source_ids": ["s9"]},
        {"title": "Chữ lồng sang trọng", "insight": "Cốc chữ lồng kèm hộp quà có hai mẫu trong top 30 cốc bán chạy trên Amazon.",
         "design_direction": "Tên đặt trong vòng tròn mảnh, phong cách chữ lồng", "source_ids": ["s1"]},
        {"title": "Huy hiệu vui tươi", "insight": "Hướng táo bạo hơn để thử nghiệm với khách thích phong cách hoài niệm; chưa có dữ liệu xác nhận.",
         "design_direction": "Huy hiệu tròn với tên trên dải băng", "source_ids": [], "basis": "hypothesis"},
    ],
}

CRITERIA = [
    {"id": "design_isolated", "label": "Bản in phẳng, tách trên nền trắng", "description": "Design is isolated flat print artwork on a plain white canvas with no product, hands, room or shadow",
     "source_requirement": "Deliver isolated flat print artwork on a plain white canvas", "required": True, "priority": 1, "weight": 10, "asset_refs": ["design"]},
    {"id": "name_exact", "label": "Chỉ có chữ ALEX, đúng chính tả", "description": "The only text is the name ALEX, spelled exactly, with no extra words, letters or numbers",
     "source_requirement": "The print shows the exact name ALEX. No extra text", "required": True, "priority": 1, "weight": 15, "asset_refs": ["design", "mockup", "video"]},
    {"id": "botanical_blue", "label": "Hoạ tiết thực vật màu xanh dương", "description": "A botanical motif in blue accompanies the name",
     "source_requirement": "with a botanical motif in blue", "required": True, "priority": 2, "weight": 10, "asset_refs": ["design"]},
    {"id": "mockup_facing", "label": "Mockup: bản in hướng về máy ảnh, nằm trọn trên cốc", "description": "Lifestyle mockup shows a ceramic mug with the whole print facing the camera and fully inside the printable area",
     "source_requirement": "a lifestyle mockup with the print facing the camera", "required": True, "priority": 2, "weight": 15, "asset_refs": ["mockup"]},
    {"id": "video_format", "label": "Video dọc 5 giây, thấy rõ sản phẩm", "description": "Video is a 5-second vertical product video in which the mug and its print are visible",
     "source_requirement": "a 5-second vertical product video", "required": True, "priority": 2, "weight": 10, "asset_refs": ["video"]},
    {"id": "video_sound", "label": "Video có âm thanh", "description": "Video includes a sound track",
     "source_requirement": "with soft background sound", "required": True, "priority": 3, "weight": 5, "asset_refs": ["video"]},
    {"id": "consistency", "label": "Tên ALEX dễ đọc và nhất quán trên mọi tài sản", "description": "Artwork and ALEX lettering stay readable and consistent across design, mockup and video",
     "source_requirement": "Keep the artwork and the ALEX lettering readable and consistent across all assets", "required": True, "priority": 1, "weight": 20, "asset_refs": ["design", "mockup", "video"]},
    {"id": "no_claims", "label": "Không nhãn hiệu, tuyên bố hay lời chứng thực", "description": "No trademarks, invented claims or customer testimonials appear",
     "source_requirement": "No extra text, trademarks, invented claims or customer testimonials", "required": True, "priority": 3, "weight": 5, "asset_refs": ["design", "mockup", "video"]},
    {"id": "mood", "label": "Cảm giác ấm áp, nhẹ nhàng, hiện đại", "description": "Overall look feels warm, calm and modern, suited to plant lovers",
     "source_requirement": "women aged 25-44 who love plants and calm, modern homes", "required": False, "priority": 5, "weight": 10, "asset_refs": ["design", "mockup", "video"]},
]
# The first plan forgot the sound requirement; the contract audit catches it before anything is generated.
FIRST_CRITERIA = [c for c in CRITERIA if c["id"] != "video_sound"]
CONTRACT_AUDITS = [
    {"summary": "Bộ tiêu chí bỏ sót yêu cầu về âm thanh của video.",
     "gaps": [{"requirement": "Video phải có âm thanh nền", "suggestion": "Thêm một tiêu chí bắt buộc về việc video có âm thanh."}],
     "unsupported": []},
    {"summary": "Bộ tiêu chí đã bao phủ mọi yêu cầu trong brief và các thiết lập của chiến dịch.", "gaps": [], "unsupported": []},
]

NO = " No product, mug, hand, room, shadow or mockup. No other text, logo or border."
MOCKUP = ("Lifestyle product photo of a matte white ceramic mug on a light neutral table in soft natural daylight, calm modern home, handle to the right. "
          "The supplied artwork is printed on the front of the mug, facing the camera, fully inside the printable area and fully readable: %s. No other objects with text.")
VIDEO = ("5-second vertical 9:16 product video of the same ceramic mug. The mug and its print are in frame from the first second with the print facing the camera. "
         "%s Soft, warm acoustic background music at low volume. No voice-over, no on-screen text, no claims.")
VARIANTS = [
    {"title": "Nhánh lá thanh mảnh", "style": "Botanical line art", "palette": ["#0F4FA8", "#FFFFFF"], "typography": "Serif cổ điển, chữ in hoa", "inspired_by": ["s5", "s6"],
     "rationale": "Đối thủ trên Shopify chủ yếu in ảnh và câu chữ dài. Một nhánh lá nét mảnh bên cạnh tên ALEX tạo sự thanh lịch, dễ in và hợp người yêu không gian tối giản.",
     "prompts": {"design": "Isolated flat print artwork centred on a plain pure white canvas: a simple minimalist botanical sprig drawn in thin blue line art, next to the name \"ALEX\" in large classic serif capitals in the same blue." + NO,
                 "mockup": MOCKUP % "a thin blue botanical sprig beside the serif name \"ALEX\"",
                 "video": VIDEO % "Slow, smooth pan across the mug."}},
    {"title": "Chữ lớn ôm thân cốc", "style": "Oversized wrap lettering", "palette": ["#0F4FA8"], "typography": "Serif đậm, nén ngang", "inspired_by": ["s9"],
     "rationale": "TikTok khuyên nêu thông điệp trong 3 giây đầu. Chữ in hoa cỡ lớn giúp tên đọc được ngay trên video dọc và tạo cá tính mạnh.",
     "prompts": {"design": "Isolated flat print artwork on a plain pure white canvas: the name \"ALEX\" in very large, bold, condensed serif capitals in deep blue, with a blue line-art botanical sprig growing between the letters L and E." + NO,
                 "mockup": MOCKUP % "very large bold blue serif capitals \"ALEX\" with a botanical sprig",
                 "video": VIDEO % "The mug turns slowly on the spot."}},
    {"title": "Vòng lá màu nước", "style": "Soft watercolour", "palette": ["#123A7D", "#3B74C4", "#7FA8DE", "#C9DCF5"], "typography": "Didone mảnh, giãn chữ", "inspired_by": ["s2", "s4"],
     "rationale": "Cốc hoa kèm tên cho bạn thân đã có trên Amazon và Etsy nhưng chưa có mẫu dẫn đầu. Vòng lá màu nước ôm quanh tên mang cảm giác mềm mại, ấm áp cho món quà tặng bạn thân.",
     "prompts": {"design": "Isolated flat print artwork on a plain pure white canvas: a loose wreath of watercolour leaves in soft shades of blue surrounding the name \"ALEX\" in elegant, widely spaced serif capitals in navy." + NO,
                 "mockup": MOCKUP % "a blue watercolour leaf wreath around the name \"ALEX\"",
                 "video": VIDEO % "The camera eases back slowly from the mug."}},
    {"title": "Huy hiệu hoài niệm", "style": "Retro badge", "palette": ["#123A7D", "#0F4FA8", "#C9DCF5"], "typography": "Sans nén, nét đậm", "inspired_by": [],
     "rationale": "Hướng táo bạo hơn để thử nghiệm, chưa có dữ liệu xác nhận. Huy hiệu tròn với tên trên dải băng mang không khí vui tươi, dễ nhận diện.",
     "prompts": {"design": "Isolated flat print artwork on a plain pure white canvas: a round retro badge in navy and blue with a scalloped edge, pale sunburst rays and small botanical sprigs, and the name \"ALEX\" in bold condensed white capitals on a navy banner across the centre." + NO,
                 "mockup": MOCKUP % "a round blue retro badge with the name \"ALEX\" on a banner",
                 "video": VIDEO % "Gentle push-in toward the badge."}},
    {"title": "Chữ lồng tối giản", "style": "Minimal monogram", "palette": ["#123A7D", "#0F4FA8", "#7FA8DE"], "typography": "Didone kết hợp sans giãn chữ", "inspired_by": ["s1"],
     "rationale": "Hai cốc chữ lồng kèm hộp quà nằm trong top 30 cốc bán chạy trên Amazon. Chữ cái đầu cỡ lớn trong vòng tròn mảnh tạo cảm giác sang trọng, hợp quà tặng.",
     "prompts": {"design": "Isolated flat print artwork on a plain pure white canvas: a thin blue double circle containing a large elegant serif initial in navy crossed by a small line-art botanical sprig, with the name \"ALEX\" in small widely spaced capitals below." + NO,
                 "mockup": MOCKUP % "a thin blue circle monogram with the name \"ALEX\" below",
                 "video": VIDEO % "Slow push-in toward the monogram."}},
]

SCREENING = {
    "summary": "Năm hướng thiết kế khác nhau rõ rệt. v1 và v3 bám sát brief nhất; v2 mạnh về độ dễ đọc nhưng cần kiểm soát kích thước; v5 có nguy cơ vi phạm yêu cầu chỉ in tên ALEX.",
    "recommended": ["v1", "v3", "v2"],
    "ranking": [
        {"id": "v1", "score": 4.8, "text_check": "pass", "strengths": "Tên ALEX rõ, nét lá mảnh cân đối, nhiều khoảng trắng nên dễ in.", "risks": "Nét lá mảnh có thể mờ khi in ở cỡ nhỏ.", "best_for": "Người thích phong cách tối giản, quà tặng thanh lịch."},
        {"id": "v2", "score": 4.3, "text_check": "pass", "strengths": "Chữ rất lớn, đọc được từ xa, hợp video dọc.", "risks": "Nhánh lá chồng lên chữ L làm chữ khó tách; bố cục rộng dễ tràn khỏi vùng in.", "best_for": "Người thích phong cách mạnh, hiện đại."},
        {"id": "v3", "score": 4.6, "text_check": "pass", "strengths": "Vòng lá màu nước mềm mại, tạo cảm giác ấm áp; tên đặt giữa rõ ràng.", "risks": "Chữ mảnh, giãn rộng có thể khó đọc khi thu nhỏ hoặc khi video chuyển động.", "best_for": "Người yêu cây cỏ, phong cách nhẹ nhàng."},
        {"id": "v4", "score": 4.0, "text_check": "pass", "strengths": "Tên nổi bật trên dải băng đậm, nhận diện nhanh.", "risks": "Nhiều chi tiết trang trí, kém tinh tế so với tinh thần tối giản của brief.", "best_for": "Người thích phong cách hoài niệm, vui tươi."},
        {"id": "v5", "score": 3.4, "text_check": "fail", "strengths": "Bố cục sang trọng, nhiều khoảng trắng.", "risks": "Chữ A lớn là ký tự thêm ngoài tên ALEX, trái với yêu cầu không có chữ thừa.", "best_for": "Quà tặng kiểu chữ lồng, nếu brief cho phép."},
    ],
}

RELEASE = [
    {"name": "Quyền sử dụng hình ảnh và phông chữ", "status": "unverified", "evidence": "Không thể xác minh bản quyền từ hình ảnh."},
    {"name": "Thông số in của nhà cung cấp (300 DPI, vùng in an toàn)", "status": "unverified", "evidence": "Ảnh AI là bản ý tưởng; tệp in cần được kiểm tra theo khuôn của nhà in."},
    {"name": "Chính sách quảng cáo của nền tảng", "status": "unverified", "evidence": "Chưa đối chiếu với chính sách hiện hành của TikTok."},
]
KEEP = "Không cần chỉnh sửa."
CLEAN = ("pass", 5, "Không có logo, nhãn hiệu, giá, lời cam kết hay lời chứng thực nào xuất hiện.", KEEP)
UNHEARD = ("unverified", 3, "Người đánh giá không nghe được âm thanh nên không thể xác nhận âm thanh có nhẹ nhàng hay không.", "Cần người nghe thử trước khi đăng.")
SOUND_OK = ("pass", 5, "Thông số tệp do hệ thống đo cho thấy video có rãnh âm thanh (mp4a).", KEEP)


def report(summary, **rows):
    return {"summary": summary, "uncovered_requirements": [], "release_checks": RELEASE,
            "checks": [dict(zip(("status", "score", "evidence", "improvement"), rows[c["id"]]), id=c["id"]) for c in CRITERIA]}


WREATH = dict(
    design_isolated=("pass", 5, "Vòng lá màu nước và chữ ALEX nằm trên nền trắng trơn, không có sản phẩm hay bóng đổ.", "Khi xuất tệp in nên dùng nền trong suốt."),
    name_exact=("pass", 5, "Chỉ có chữ “ALEX” ở giữa vòng lá; gạch mảnh bên dưới là nét trang trí, không phải ký tự.", KEEP),
    botanical_blue=("pass", 4.5, "Vòng lá gồm nhiều sắc xanh dương từ nhạt đến đậm; lá được gợi tả bằng mảng màu nước nên ít chi tiết.", "Thêm vài gân lá để hoạ tiết thực vật rõ hơn."),
    mockup_facing=("pass", 5, "Bản in nằm giữa mặt trước của cốc, quay về máy ảnh và không chạm mép.", KEEP),
    no_claims=CLEAN,
    mood=("pass", 5, "Màu nước loang nhẹ và nền sáng tạo cảm giác êm dịu, hợp người yêu cây cỏ.", KEEP),
)
BLURRED = "Trong video, nét chữ mảnh của ALEX còn mờ ở khoảng 2 giây đầu khi máy quay di chuyển; chỉ đọc rõ ở nửa sau."
WREATH_TWO = dict(WREATH,
    video_format=("pass", 4.5, "Video dọc khoảng 5 giây, máy quay tiến gần dần vào bản in; cốc luôn trong khung hình.", "Bắt đầu ở cự ly gần hơn để bản in lớn ngay từ đầu."),
    video_sound=SOUND_OK, sound_soft=UNHEARD)
LETTERS = dict(
    design_isolated=("pass", 5, "Bản thiết kế là chữ ALEX cỡ lớn cùng nhánh lá trên nền trắng, không có sản phẩm hay bóng đổ.", KEEP),
    video_sound=SOUND_OK, no_claims=CLEAN, sound_soft=UNHEARD,
    mood=("pass", 4, "Chữ lớn, tương phản mạnh tạo cảm giác hiện đại nhưng kém nhẹ nhàng hơn các hướng khác.", "Thêm khoảng trắng quanh chữ để bố cục mềm hơn."),
)

BADGE = dict(
    design_isolated=("pass", 5, "Huy hiệu tròn cùng chữ ALEX nằm trên nền trắng trơn, không có sản phẩm hay bóng đổ.", KEEP),
    name_exact=("pass", 5, "Chỉ có chữ “ALEX” màu trắng trên dải băng xanh đậm; không có chữ hay số nào khác.", KEEP),
    botanical_blue=("pass", 4.5, "Bốn nhánh lá nhỏ màu xanh dương đặt phía trên và dưới dải băng; hoạ tiết thực vật có nhưng không phải điểm nhấn chính.", "Tăng kích thước nhánh lá để hoạ tiết thực vật rõ hơn."),
    mockup_facing=("pass", 5, "Huy hiệu nằm giữa mặt trước cốc, quay về máy ảnh và không chạm mép.", KEEP),
    video_format=("pass", 4.5, "Video dọc khoảng 5 giây, máy quay tiến gần chậm; cốc và huy hiệu luôn trong khung hình.", KEEP),
    video_sound=SOUND_OK,
    consistency=("pass", 5, "Chữ trắng trên nền xanh đậm đọc rõ ở cả ba tài sản; hình dạng huy hiệu giữ nguyên.", KEEP),
    no_claims=CLEAN,
    mood=("pass", 3.5, "Huy hiệu nhiều chi tiết và tương phản mạnh, vui tươi hơn là nhẹ nhàng, tối giản.", "Giảm số tia nền và viền răng cưa để bố cục thoáng hơn."),
    sound_soft=UNHEARD,
)
MONOGRAM = dict(
    design_isolated=("pass", 5, "Vòng tròn mảnh, chữ và nhánh lá nằm trên nền trắng trơn, không có sản phẩm hay bóng đổ.", KEEP),
    botanical_blue=("pass", 4.5, "Nhánh lá nét mảnh màu xanh dương đi cùng chữ; kích thước nhỏ so với chữ.", "Tăng nhẹ kích thước nhánh lá."),
    mockup_facing=("pass", 5, "Bản in nằm giữa mặt trước cốc, quay về máy ảnh và không chạm mép.", KEEP),
    video_sound=SOUND_OK, no_claims=CLEAN, sound_soft=UNHEARD,
    mood=("pass", 4.5, "Đường nét mảnh và nhiều khoảng trắng tạo cảm giác thanh lịch, nhẹ nhàng.", KEEP),
)

# Reviewer answers for every design and round, whichever designs the customer takes forward.
REVIEWS = {
    "v1": [{"evaluation": report(
        "Bộ tài sản bám sát brief: tên ALEX chính xác, hoạ tiết lá xanh nhất quán, mockup và video rõ ràng. Tất cả tiêu chí đều đạt.",
        design_isolated=("pass", 5, "Ảnh thiết kế chỉ gồm nhánh lá và chữ ALEX trên nền trắng trơn; không có sản phẩm, bàn tay hay bóng đổ.", "Khi xuất tệp in nên dùng nền trong suốt."),
        name_exact=("pass", 5, "Trên cả ba tài sản chỉ có bốn chữ in hoa “ALEX”, đúng chính tả; không thấy chữ, số hay ký hiệu nào khác.", KEEP),
        botanical_blue=("pass", 5, "Nhánh lá vẽ nét mảnh màu xanh dương đặt bên trái tên, cùng tông màu với chữ.", "Có thể tăng nhẹ độ dày nét để in sắc hơn trên gốm."),
        mockup_facing=("pass", 5, "Cốc gốm trắng đặt trên mặt bàn sáng, bản in quay thẳng về máy ảnh và nằm gọn giữa thân cốc.", KEEP),
        video_format=("pass", 4.5, "Video dọc dài khoảng 5 giây, máy quay lia chậm qua thân cốc. Ở giây đầu tên bị khuất một phần bên phải, sau đó hiện đầy đủ.", "Bắt đầu video khi cả tên đã nằm trong khung hình."),
        video_sound=SOUND_OK,
        consistency=("pass", 5, "Kiểu chữ serif, màu xanh và nhánh lá giống nhau trên bản thiết kế, mockup và video; tên đọc rõ ở cả ba.", KEEP),
        no_claims=CLEAN,
        mood=("pass", 4.5, "Nền kem sáng, ánh sáng tự nhiên và hoạ tiết lá tạo cảm giác nhẹ nhàng, hiện đại.", "Thêm một chi tiết cây xanh mờ ở hậu cảnh để gần gũi hơn với người yêu cây."),
        sound_soft=UNHEARD)}],
    "v2": [
        {"evaluation": report("Kiểu chữ lớn nổi bật nhưng bản in tràn khỏi thân cốc, khiến tên không đọc trọn vẹn trên mockup và video.", **dict(LETTERS,
            name_exact=("pass", 4, "Chữ trên bản thiết kế là “ALEX”; trên mockup chữ A và X bị khuất một phần ở mép cốc nhưng không có ký tự thừa.", "Thu nhỏ bản in để cả bốn chữ hiện trọn vẹn."),
            botanical_blue=("pass", 5, "Nhánh lá xanh dương nằm giữa chữ L và E, cùng màu với chữ.", KEEP),
            mockup_facing=("fail", 1.5, "Bản in rộng hơn thân cốc: chữ A và chữ X tràn ra ngoài hai mép, không nằm trọn trong vùng in.", "Thu nhỏ bản in còn khoảng 80% bề ngang mặt trước của cốc."),
            video_format=("pass", 4, "Video dọc khoảng 5 giây, máy quay di chuyển chậm; sản phẩm luôn trong khung hình.", "Giữ bản in ở chính giữa khung hình."),
            consistency=("fail", 2, "Ở đầu video chỉ thấy “LEX” vì chữ A nằm khuất ở mép cốc; tên không đọc trọn vẹn trên mockup và video.", "Giữ cả bốn chữ ở mặt trước cốc trong suốt video.")))},
        {"evaluation": report("Sau khi thu nhỏ bản in, tên ALEX hiện trọn vẹn và đọc rõ; bộ tài sản đạt mọi tiêu chí bắt buộc.", **dict(LETTERS,
            name_exact=("pass", 5, "Cả bốn chữ ALEX hiện đầy đủ trên thiết kế, mockup và video; không có ký tự thừa.", KEEP),
            botanical_blue=("pass", 4.5, "Nhánh lá xanh dương vẫn ở giữa tên nhưng chồng lên chân chữ L nên hơi khó tách khỏi chữ.", "Tách nhánh lá khỏi chữ L một khoảng nhỏ."),
            mockup_facing=("pass", 5, "Bản in đã thu gọn, nằm trọn ở mặt trước cốc và quay về máy ảnh.", KEEP),
            video_format=("pass", 4.5, "Video dọc khoảng 5 giây, máy quay tiến gần chậm; cốc và bản in luôn trong khung hình.", KEEP),
            consistency=("pass", 4.5, "Tên ALEX đọc rõ trên cả ba tài sản; kiểu chữ và màu xanh nhất quán.", "Tăng nhẹ khoảng cách giữa chữ L và E.")))}],
    "v3": [
        {"evaluation": report("Thiết kế và mockup đạt yêu cầu, nhưng video thiếu âm thanh và tên khó đọc khi chuyển động.", **dict(WREATH,
            video_format=("pass", 4, "Video dọc khoảng 5 giây, máy quay lùi chậm; cốc luôn trong khung hình nhưng bản in nhỏ dần.", "Dùng chuyển động tiến gần để bản in lớn dần."),
            video_sound=("fail", 0, "Thông số tệp do hệ thống đo cho thấy video không có rãnh âm thanh.", "Tạo lại video với âm thanh nền."),
            consistency=("fail", 2.5, "Trên mockup tên đọc được, nhưng trong video nét chữ mảnh và giãn rộng khiến “ALEX” mờ, khó đọc khi cốc ở xa.", "Đưa máy quay lại gần hơn hoặc tăng độ đậm của chữ trong bản in."),
            sound_soft=("unverified", 2, "Video không có âm thanh nên không có gì để đánh giá.", "Đánh giá lại sau khi video có âm thanh.")))},
        {"evaluation": report("Âm thanh đã có và bố cục đẹp; tên ALEX đọc được ở cuối video.", **dict(WREATH_TWO,
            consistency=("pass", 4.5, "Tên ALEX đọc được ở cuối video; ở 2 giây đầu nét chữ mảnh còn mờ khi máy quay di chuyển.", "Bắt đầu video ở cự ly gần hơn."))),
         "audit": {"conflicts": [{"id": "consistency", "reason": "Bằng chứng nêu tên còn mờ ở 2 giây đầu nhưng kết luận lại là đạt; yêu cầu là tên phải dễ đọc trên mọi tài sản."}], "uncovered_requirements": []},
         "adjudication": dict(report("Âm thanh đã có và bố cục đẹp, nhưng tên vẫn khó đọc ở đầu video nên tiêu chí bắt buộc về độ dễ đọc chưa đạt.", **dict(WREATH_TWO,
            consistency=("fail", 3.5, BLURRED, "Tăng độ đậm nét chữ trong bản in hoặc bắt đầu video ở cự ly gần."))),
            resolutions=[{"id": "consistency", "resolved": True, "reason": "Xem lại video: trong khoảng 2 giây đầu nét chữ mảnh không đọc rõ, nên tiêu chí bắt buộc chưa đạt."}])}],
    "v4": [{"evaluation": report("Huy hiệu rõ ràng, tên ALEX đọc tốt trên mọi tài sản. Phong cách vui tươi hơn so với tinh thần nhẹ nhàng của brief.", **BADGE)}],
    "v5": [
        {"evaluation": report("Bố cục thanh lịch nhưng chữ A cỡ lớn là ký tự thêm ngoài tên ALEX, trái với yêu cầu chỉ in đúng tên.", **dict(MONOGRAM,
            name_exact=("fail", 1.5, "Ngoài chữ “ALEX” ở phía dưới còn có một chữ “A” rất lớn trong vòng tròn; đây là ký tự thêm ngoài tên.", "Bỏ chữ cái lớn và đặt tên ALEX vào giữa vòng tròn."),
            video_format=("pass", 4.5, "Video dọc khoảng 5 giây, máy quay lùi chậm; cốc và bản in luôn trong khung hình.", KEEP),
            consistency=("pass", 4, "Bản in giống nhau trên ba tài sản; chữ ALEX nhỏ bên dưới khó đọc hơn chữ A lớn.", "Tăng cỡ chữ của tên ALEX.")))},
        {"evaluation": report("Bản vẽ lại chỉ còn tên ALEX trong vòng tròn cùng hai nhánh lá; mọi tiêu chí bắt buộc đều đạt.", **dict(MONOGRAM,
            name_exact=("pass", 5, "Chỉ có bốn chữ “ALEX” ở giữa vòng tròn; chữ cái lớn đã được bỏ.", KEEP),
            video_format=("pass", 4.5, "Video dọc khoảng 5 giây, máy quay tiến gần chậm; cốc và bản in luôn trong khung hình.", KEEP),
            consistency=("pass", 4.5, "Tên ALEX đọc rõ trên bản vẽ mới, mockup và video; vòng tròn và nhánh lá nhất quán.", KEEP)))}],
}
AGREE = {"conflicts": [], "uncovered_requirements": []}

REVISIONS = {
    "v3": {"video": VIDEO % "The camera starts close and pushes in slowly toward the wreath so the name stays large and readable.",
           "changes": "Tạo lại video có âm thanh nền và cho máy quay tiến gần để tên ALEX lớn, dễ đọc hơn."},
    "v2": {"mockup": MOCKUP % "bold blue serif capitals \"ALEX\" with a botanical sprig, scaled to about 80% of the width of the mug front so all four letters are visible",
           "video": VIDEO % "Slow push-in; all four letters of the name stay on the front of the mug for the whole video.",
           "changes": "Thu nhỏ bản in để nằm trọn ở mặt trước cốc và giữ cả bốn chữ trong khung hình suốt video."},
    "v5": {"design": "Isolated flat print artwork on a plain pure white canvas: a thin blue double circle containing only the name \"ALEX\" in elegant serif capitals in navy, with two small line-art botanical sprigs curving below it. No initial, no monogram letter." + NO,
           "mockup": MOCKUP % "a thin blue circle containing the name \"ALEX\" with two small sprigs",
           "video": VIDEO % "Slow push-in toward the circle.",
           "changes": "Vẽ lại bản in: bỏ chữ A cỡ lớn, đặt tên ALEX vào giữa vòng tròn để chỉ còn đúng tên theo brief."},
}

SEARCHES = ["personalized mug gift for best friend Christmas", "Amazon best sellers novelty coffee mugs", "personalized birth flower name mug best friend gift",
            "Etsy personalized best friends mug", "NRF holiday survey 2025 gifts", "print on demand holiday order deadlines 2026",
            "print on demand products mugs 2026", "print file DPI for mugs"]
# Competitors only; the customer's own store is never studied as one.
STORES = ["wanderprints.com", "pawfecthouse.com", "trendingcustom.com", "westandwillow.com"]
