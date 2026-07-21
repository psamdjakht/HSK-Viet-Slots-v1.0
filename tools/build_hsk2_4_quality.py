#!/usr/bin/env python3
"""Build additive quality packs for HSK 2–4 without modifying the HSK 1 pack."""
from __future__ import annotations
import json, re, unicodedata
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
LEVELS = (2, 3, 4)
TODAY = '2026-07-21'

BAD_PREFIX = re.compile(r'^(LT:|Lượng từ:|biến thể|xem\s|cũng viết|cũng đọc|họ\s+[A-ZÀ-Ỹ])', re.I)
MEASURE_RE = re.compile(r'(?:LT:|Lượng từ:)\s*([^;，。)]+)', re.I)

PRIMARY_OVERRIDES = {
    # Các mục phổ biến dễ bị từ điển chọn nghĩa phụ/tên riêng trước.
    '成功': 'thành công', '和平': 'hòa bình', '凉': 'mát; lạnh', '孙子': 'cháu trai',
    '通': 'thông; thông suốt', '安排': 'sắp xếp; bố trí', '保证': 'bảo đảm',
    '标准': 'tiêu chuẩn', '表扬': 'khen ngợi', '材料': 'tài liệu; vật liệu',
    '产生': 'sinh ra; nảy sinh', '尝试': 'thử; thử nghiệm', '程度': 'mức độ',
    '处理': 'xử lý', '打扰': 'làm phiền', '打招呼': 'chào hỏi', '调查': 'điều tra; khảo sát',
    '发展': 'phát triển', '反对': 'phản đối', '方式': 'phương thức; cách thức',
    '丰富': 'phong phú; làm phong phú', '负责': 'phụ trách; chịu trách nhiệm',
    '改变': 'thay đổi', '感动': 'cảm động; làm cảm động', '感谢': 'cảm ơn; biết ơn',
    '关系': 'quan hệ; mối quan hệ', '规定': 'quy định', '过程': 'quá trình',
    '获得': 'đạt được; giành được', '积极': 'tích cực', '坚持': 'kiên trì',
    '减少': 'giảm bớt', '交流': 'giao lưu; trao đổi', '接受': 'tiếp nhận; chấp nhận',
    '进行': 'tiến hành', '经历': 'trải qua; kinh nghiệm', '精神': 'tinh thần',
    '举办': 'tổ chức', '拒绝': 'từ chối', '考虑': 'cân nhắc; suy nghĩ',
    '联系': 'liên hệ', '理解': 'hiểu; thông cảm', '厉害': 'lợi hại; giỏi; nghiêm trọng',
    '另外': 'ngoài ra', '留下': 'để lại; ở lại', '麻烦': 'phiền phức; làm phiền',
    '耐心': 'kiên nhẫn', '判断': 'phán đoán; đánh giá', '陪': 'đi cùng; đi kèm',
    '批评': 'phê bình', '情况': 'tình hình; trường hợp', '取': 'lấy; nhận',
    '缺点': 'khuyết điểm', '任务': 'nhiệm vụ', '商量': 'bàn bạc', '适合': 'phù hợp',
    '说明': 'giải thích; thuyết minh', '顺利': 'thuận lợi', '态度': 'thái độ',
    '提供': 'cung cấp', '条件': 'điều kiện', '同意': 'đồng ý', '完成': 'hoàn thành',
    '无论': 'bất luận; dù', '误会': 'hiểu lầm', '吸引': 'thu hút', '效果': 'hiệu quả',
    '选择': 'lựa chọn', '邀请': 'mời', '影响': 'ảnh hưởng', '原来': 'hóa ra; ban đầu',
    '原因': 'nguyên nhân', '允许': 'cho phép', '责任': 'trách nhiệm', '正常': 'bình thường',
    '证明': 'chứng minh', '支持': 'ủng hộ; hỗ trợ', '值得': 'đáng; đáng để',
}

SPECIAL_NOTES = {
    '把': 'Đưa tân ngữ lên trước động từ để nhấn mạnh cách xử lý và kết quả; sau động từ thường cần thành phần bổ sung.',
    '被': 'Đánh dấu câu bị động; chủ thể chịu tác động đứng trước 被, tác nhân có thể lược khi đã rõ.',
    '得': 'Đặt sau động từ để nối với bổ ngữ mức độ hoặc trạng thái; phân biệt với 的 và 地.',
    '地': 'Đặt sau trạng ngữ, thường là tính từ/cụm miêu tả, rồi mới đến động từ; phân biệt với 的 và 得.',
    '过': 'Sau động từ có thể chỉ kinh nghiệm từng trải; không dùng khi nói một thời điểm quá khứ cụ thể đã kết thúc theo cách kể thông thường.',
    '着': 'Sau động từ chỉ trạng thái đang duy trì; khác 正在 là nhấn mạnh hành động đang diễn ra.',
    '才': 'Nhấn mạnh muộn, ít hoặc điều kiện khó mới đạt được; thường mang sắc thái trái kỳ vọng.',
    '就': 'Nhấn mạnh sớm, nhanh, dễ hoặc kết quả xảy ra ngay khi điều kiện được đáp ứng.',
    '又': 'Dùng cho hành động/tình trạng đã lặp lại; việc lặp lại trong tương lai thường dùng 再.',
    '再': 'Dùng cho hành động sẽ lặp lại hoặc tiếp tục trong tương lai; khác 又 thường nói việc đã xảy ra.',
    '还是': 'Trong câu hỏi lựa chọn nghĩa là “hay là”; trong câu trần thuật có thể mang nghĩa “vẫn; tốt hơn nên”.',
    '或者': 'Nối các lựa chọn trong câu trần thuật; câu hỏi lựa chọn thường dùng 还是.',
    '除了': 'Thường đi với 以外/之外 và còn có 还/也/都 để biểu thị bổ sung hoặc ngoại lệ.',
    '尽管': 'Mở đầu vế nhượng bộ, thường đi cùng 但是/可是/然而 ở vế sau.',
    '只要': 'Nêu điều kiện đủ, thường đi với 就 ở vế kết quả.',
    '只有': 'Nêu điều kiện cần hoặc duy nhất, thường đi với 才 ở vế kết quả.',
    '即使': 'Nêu giả định nhượng bộ, thường đi với 也/还 ở vế sau.',
    '由于': 'Nêu nguyên nhân theo sắc thái văn viết hơn 因为; thường đi với 因此/所以.',
    '对于': 'Đưa đối tượng được bàn luận lên đầu câu; sau đó là nhận xét hoặc thái độ đối với đối tượng đó.',
    '关于': 'Giới thiệu chủ đề/nội dung liên quan; khác 对于 là không nhất thiết biểu thị thái độ tác động lên đối tượng.',
    '按照': 'Nêu căn cứ, quy tắc hoặc phương thức để thực hiện hành động.',
    '通过': 'Có thể chỉ thông qua phương tiện/cách thức hoặc đi xuyên qua một nơi.',
    '甚至': 'Đưa ra trường hợp cao hơn hoặc bất ngờ hơn so với thông tin trước.',
    '反而': 'Biểu thị kết quả trái với dự đoán hoặc trái với điều vừa nêu.',
    '本来': 'Nói tình trạng hoặc ý định vốn có trước khi xuất hiện sự thay đổi.',
    '原来': 'Có thể nghĩa là “hóa ra” khi phát hiện sự thật, hoặc “ban đầu; vốn”.',
}

TOPIC_KEYWORDS = {
    'gia đình & quan hệ': ['gia đình','bố','mẹ','anh','chị','em','vợ','chồng','con','cháu','họ hàng','quan hệ','bạn bè','đồng nghiệp','hàng xóm'],
    'học tập & ngôn ngữ': ['học','giáo viên','học sinh','sinh viên','bài','thi','ngôn ngữ','chữ','đọc','viết','giải thích','kiến thức','trường'],
    'công việc & kinh doanh': ['công việc','công ty','kinh doanh','nhân viên','quản lý','nghề','lương','nhiệm vụ','họp','phỏng vấn','hợp đồng'],
    'ăn uống & nhà hàng': ['ăn','uống','món','thức ăn','đồ ăn','nhà hàng','cơm','trà','cà phê','rau','thịt','cá','vị'],
    'đi lại & du lịch': ['du lịch','đi lại','xe','tàu','máy bay','đường','ga','sân bay','khách sạn','vé','hành lý','lái'],
    'thời gian & lịch': ['thời gian','ngày','tuần','tháng','năm','giờ','phút','sớm','muộn','lịch','quá khứ','tương lai'],
    'địa điểm & phương hướng': ['địa điểm','nơi','phía','hướng','trong','ngoài','trên','dưới','gần','xa','thành phố','nông thôn'],
    'sức khỏe & cơ thể': ['sức khỏe','bệnh','đau','thuốc','bác sĩ','cơ thể','mệt','ngủ','tập thể dục','an toàn','tai nạn'],
    'cảm xúc & tính cách': ['cảm xúc','vui','buồn','giận','sợ','lo','thất vọng','hạnh phúc','tính cách','thái độ','kiên nhẫn','cảm động'],
    'xã hội & giao tiếp': ['xã hội','giao tiếp','chào','cảm ơn','xin lỗi','mời','thảo luận','trao đổi','liên hệ','tin tức','văn hóa'],
    'mua sắm & tài chính': ['mua','bán','tiền','giá','rẻ','đắt','ngân hàng','thanh toán','thu nhập','chi phí','hóa đơn'],
    'nhà cửa & đồ vật': ['nhà','phòng','đồ vật','bàn','ghế','cửa','quần áo','máy','thiết bị','điện thoại','máy tính'],
    'thiên nhiên & môi trường': ['thời tiết','mưa','nắng','gió','mùa','nhiệt độ','cây','hoa','động vật','môi trường','khí hậu'],
    'khoa học & công nghệ': ['khoa học','kỹ thuật','công nghệ','internet','mạng','dữ liệu','nghiên cứu','phát minh'],
    'pháp luật & tổ chức': ['pháp luật','quy định','chính phủ','tổ chức','quyền','trách nhiệm','tiêu chuẩn','chính sách'],
    'tư duy & đánh giá': ['suy nghĩ','hiểu','biết','nhớ','quên','phán đoán','lý do','nguyên nhân','kết quả','ý kiến','quan điểm','mục đích'],
    'hành động & quá trình': ['làm','thực hiện','tiến hành','bắt đầu','kết thúc','thay đổi','phát triển','tăng','giảm','xử lý','chuẩn bị','hoàn thành'],
    'miêu tả & mức độ': ['tính chất','mức độ','rất','khá','đặc biệt','bình thường','quan trọng','phù hợp','đúng','sai','dễ','khó'],
}

CURATED_COLLOCATIONS = {
    '安排':['安排时间','安排工作','提前安排'], '保证':['保证安全','保证质量','我保证'],
    '标准':['达到标准','生活标准','按照标准'], '表示':['表示感谢','表示同意','表示欢迎'],
    '表扬':['受到表扬','表扬学生','公开表扬'], '参加':['参加活动','参加考试','参加会议'],
    '成功':['取得成功','成功完成','非常成功'], '处理':['处理问题','及时处理','处理事情'],
    '发展':['经济发展','快速发展','发展机会'], '负责':['负责工作','对…负责','认真负责'],
    '改变':['改变计划','发生改变','改变看法'], '感动':['让人感动','深受感动','感动得哭了'],
    '关系':['保持关系','没有关系','人际关系'], '过程':['学习过程','工作过程','整个过程'],
    '获得':['获得机会','获得成功','获得帮助'], '积极':['积极参加','积极作用','态度积极'],
    '坚持':['坚持学习','坚持到底','一直坚持'], '交流':['交流经验','文化交流','互相交流'],
    '接受':['接受意见','接受邀请','容易接受'], '进行':['进行调查','进行讨论','顺利进行'],
    '经历':['亲身经历','工作经历','经历困难'], '举办':['举办活动','举办比赛','成功举办'],
    '考虑':['认真考虑','考虑问题','考虑一下'], '联系':['保持联系','联系朋友','取得联系'],
    '理解':['理解意思','互相理解','容易理解'], '麻烦':['麻烦你','遇到麻烦','很麻烦'],
    '判断':['作出判断','判断正确','根据…判断'], '批评':['受到批评','批评别人','提出批评'],
    '情况':['了解情况','实际情况','特殊情况'], '商量':['商量一下','和家人商量','共同商量'],
    '适合':['适合学习','适合你','不太适合'], '说明':['说明情况','使用说明','这说明'],
    '顺利':['顺利完成','一切顺利','进展顺利'], '提供':['提供帮助','提供服务','提供机会'],
    '条件':['生活条件','满足条件','有条件'], '同意':['同意意见','同意参加','不同意'],
    '完成':['完成任务','按时完成','顺利完成'], '影响':['影响工作','受到影响','产生影响'],
    '选择':['作出选择','选择专业','正确选择'], '邀请':['邀请朋友','接受邀请','正式邀请'],
    '允许':['允许进入','不允许','条件允许'], '支持':['支持工作','得到支持','互相支持'],
}


def clean_text(text: str) -> str:
    text = str(text or '')
    text = re.sub(r'LT:[^;，。)]*', '', text)
    text = re.sub(r'\(lượng từ:[^)]*\)', '', text, flags=re.I)
    text = re.sub(r'^\((?:thông tục|văn học|khẩu ngữ|cổ)\)\s*', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip(' ;，,')
    return text


def normalize_senses(word: dict) -> tuple[str, list[str], list[str]]:
    kept: list[str] = []
    measures: list[str] = []
    for sense in word.get('senses', []):
        raw = str(sense.get('vi', ''))
        for match in MEASURE_RE.findall(raw):
            measures.extend(re.findall(r'[\u4e00-\u9fff]+', match)[:4])
        text = clean_text(raw)
        if not text or BAD_PREFIX.match(text):
            continue
        if text not in kept:
            kept.append(text)
    override = PRIMARY_OVERRIDES.get(word['simplified'])
    if override:
        primary = override
        override_parts = [x.strip() for x in override.split(';') if x.strip()]
        kept = override_parts + [x for x in kept if x not in override_parts]
    else:
        if not kept:
            kept = [clean_text(word.get('meaning', '')) or 'Cần bổ sung nghĩa']
        primary = '; '.join([x.strip() for x in kept[0].split(';')[:3] if x.strip()])
    return primary, kept[:10], list(dict.fromkeys(measures))


def folded(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', str(text).lower()) if unicodedata.category(c) != 'Mn')


def topic_for(word: dict, primary: str, senses: list[str]) -> str:
    haystack = ' '.join([primary, *senses]).lower()
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            pattern = r'(?<!\w)' + re.escape(keyword.lower()) + r'(?!\w)'
            if re.search(pattern, haystack):
                score += 2 + min(2, len(keyword) // 6)
        scores[topic] = score
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    poses = set(word.get('pos') or [])
    if poses & {'trợ từ','giới từ','liên từ','phó từ','đại từ','số từ','lượng từ'}:
        return 'từ chức năng & ngữ pháp'
    if 'động từ' in poses:
        return 'hành động & quá trình'
    if 'tính từ' in poses:
        return 'miêu tả & mức độ'
    if 'danh từ' in poses:
        return 'sự vật & khái niệm'
    return 'từ vựng tổng hợp'


def usage_note(word: dict, level: int, topic: str, measures: list[str]) -> str:
    s = word['simplified']
    if s in SPECIAL_NOTES:
        return SPECIAL_NOTES[s]
    poses = ', '.join(word.get('pos') or []) or 'từ'
    if measures:
        return f'{s} thường dùng như {poses}. Lượng từ ghi nhận trong dữ liệu: {", ".join(measures)}; cần đối chiếu ngữ cảnh cụ thể.'
    if 'động từ' in (word.get('pos') or []):
        return f'{s} là động từ HSK {level}; nên học cùng tân ngữ, bổ ngữ và cụm từ thường đi kèm thay vì học riêng lẻ.'
    if 'tính từ' in (word.get('pos') or []):
        return f'{s} là tính từ HSK {level}; chú ý vị trí vị ngữ, phó từ mức độ và ngữ cảnh so sánh khi sử dụng.'
    if 'phó từ' in (word.get('pos') or []):
        return f'{s} là phó từ HSK {level}; vị trí trong câu và phạm vi bổ nghĩa quyết định sắc thái.'
    if {'trợ từ','giới từ','liên từ'} & set(word.get('pos') or []):
        return f'{s} là từ chức năng HSK {level}; cần học theo mẫu câu hoàn chỉnh vì nghĩa phụ thuộc cấu trúc.'
    return f'{s} là {poses} thuộc HSK {level}, chủ đề {topic}; ưu tiên nghĩa thông dụng và kiểm tra lại khi gặp nghĩa chuyên ngành.'


def similarity(a: dict, b: dict) -> int:
    score = 0
    pa = re.sub(r'\d|\s', '', a.get('pinyinNumbered', ''))
    pb = re.sub(r'\d|\s', '', b.get('pinyinNumbered', ''))
    if a.get('pinyinNumbered') == b.get('pinyinNumbered'): score += 12
    elif pa and pa == pb: score += 8
    score += len(set(a['simplified']) & set(b['simplified'])) * 4
    if set(a.get('pos', [])) & set(b.get('pos', [])): score += 3
    if a.get('_topic') == b.get('_topic'): score += 2
    ma = set(re.findall(r'[A-Za-zÀ-ỹ]+', a.get('_primary','').lower()))
    mb = set(re.findall(r'[A-Za-zÀ-ỹ]+', b.get('_primary','').lower()))
    score += min(4, len(ma & mb))
    return score


def make_pack(level: int) -> dict:
    payload = json.loads((ROOT / f'data/levels/hsk{level}.json').read_text(encoding='utf-8'))
    prepared = []
    for word in payload['words']:
        primary, senses, measures = normalize_senses(word)
        row = dict(word)
        row['_primary'], row['_senses'], row['_measures'] = primary, senses, measures
        row['_topic'] = topic_for(word, primary, senses)
        prepared.append(row)
    quality = {}
    for word in prepared:
        ranked = sorted((x for x in prepared if x['id'] != word['id']), key=lambda x: (-similarity(word, x), x['id']))
        confusables = []
        for candidate in ranked:
            if similarity(word, candidate) < 5:
                break
            if candidate['simplified'] not in confusables:
                confusables.append(candidate['simplified'])
            if len(confusables) >= 5:
                break
        base_example = word.get('example')
        grammar_example = None
        for item in globals().get('GRAMMAR', {}).get(level, []):
            sample = (item.get('examples') or [{}])[0]
            marker = f"{item.get('title','')} {item.get('formula','')}"
            if word['simplified'] in marker and word['simplified'] in sample.get('zh', ''):
                grammar_example = sample
                break
        if base_example:
            example = {**base_example, 'kind': 'usage', 'exerciseEligible': True}
        elif grammar_example:
            example = {**grammar_example, 'status': 'bien_soan_ngu_phap', 'kind': 'usage', 'exerciseEligible': True}
        else:
            example = {
                'zh': f'请读这个词：“{word["simplified"]}”。',
                'pinyin': f'Qǐng dú zhège cí: “{word["pinyin"]}”.',
                'vi': f'Hãy đọc từ “{word["simplified"]}”.',
                'status': 'mau_doc_tu', 'kind': 'pronunciation', 'exerciseEligible': False
            }
        quality[word['id']] = {
            'wordId': word['id'], 'primaryMeaning': word['_primary'], 'normalizedSenses': word['_senses'],
            'pos': word.get('pos') or [], 'topic': word['_topic'], 'measureWords': word['_measures'],
            'usageNote': usage_note(word, level, word['_topic'], word['_measures']),
            'collocations': CURATED_COLLOCATIONS.get(word['simplified'], []),
            'confusables': confusables, 'example': example,
            'standardization': {
                'version': f'HSK{level}-Q1', 'status': 'chuan_hoa_he_thong',
                'reviewedBy': 'đối chiếu chữ–pinyin + làm sạch nghĩa + quy tắc ngữ cảnh', 'updatedAt': TODAY
            }
        }
    return {
        'meta': {
            'level': str(level), 'version': '4.0.0', 'wordCount': len(quality),
            'description': f'Lớp chuẩn hóa HSK {level}: làm sạch nghĩa, từ loại, chủ đề, ghi chú cách dùng, từ dễ nhầm và ví dụ an toàn.'
        },
        'words': quality
    }


def gi(code, title, formula, explanation, zh, pinyin, vi, mistake):
    return {'id': code, 'title': title, 'formula': formula, 'explanation': explanation,
            'examples': [{'zh': zh, 'pinyin': pinyin, 'vi': vi}], 'mistake': mistake}

GRAMMAR = {
2: [
 gi('G2-01','Đã từng với 过','V + 过 + O','Diễn tả kinh nghiệm đã từng có, không nhấn mạnh thời điểm cụ thể.','我去过北京。','Wǒ qùguo Běijīng.','Tôi đã từng đến Bắc Kinh.','Không dùng 过 để kể một sự việc quá khứ có thời điểm cụ thể khi chỉ muốn nói hành động đã hoàn tất.'),
 gi('G2-02','Đang diễn ra với 正在','S + 正在 + V + O','Nhấn mạnh hành động đang diễn ra tại thời điểm nói.','他正在做作业。','Tā zhèngzài zuò zuòyè.','Cậu ấy đang làm bài tập.','Không đặt 了 chỉ hoàn thành ngay sau động từ đang diễn ra.'),
 gi('G2-03','Trạng thái duy trì với 着','V + 着 + trạng thái','Diễn tả tư thế hoặc trạng thái đang được duy trì.','门开着。','Mén kāizhe.','Cửa đang mở.','Không đồng nhất 着 với 正在; 着 thiên về trạng thái duy trì.'),
 gi('G2-04','Hành động sắp xảy ra','快/要/快要…了','Diễn tả sự việc sắp xảy ra; 了 đặt cuối câu báo hiệu thay đổi gần kề.','火车快要到了。','Huǒchē kuàiyào dào le.','Tàu sắp đến rồi.','Không dùng trước một mốc thời gian còn rất xa.'),
 gi('G2-05','So sánh với 比','A + 比 + B + Adj','So sánh A có tính chất hơn B.','今天比昨天冷。','Jīntiān bǐ zuótiān lěng.','Hôm nay lạnh hơn hôm qua.','Không đặt 很 trực tiếp sau tính từ trong cấu trúc so sánh cơ bản.'),
 gi('G2-06','Không bằng với 没有','A + 没有 + B + Adj','Nói A không đạt mức độ như B.','我没有他高。','Wǒ méiyǒu tā gāo.','Tôi không cao bằng anh ấy.','Không dùng 不有; phủ định 有 là 没有.'),
 gi('G2-07','Càng hơn với 更','S + 更 + Adj/V','So sánh ngầm với một chuẩn đã biết và nhấn mạnh mức độ cao hơn.','这个办法更简单。','Zhège bànfǎ gèng jiǎndān.','Cách này đơn giản hơn.','Cần có ngữ cảnh hoặc đối tượng so sánh ngầm.'),
 gi('G2-08','Tốt nhất với 最','S + 最 + Adj/V','Biểu thị mức cao nhất trong phạm vi được hiểu.','她唱得最好。','Tā chàng de zuì hǎo.','Cô ấy hát hay nhất.','Phải xác định hoặc ngầm hiểu phạm vi so sánh.'),
 gi('G2-09','Bổ ngữ mức độ với 得','V + 得 + Adj','Đánh giá mức độ hoặc trạng thái của hành động.','他说得很快。','Tā shuō de hěn kuài.','Anh ấy nói rất nhanh.','Không viết 的/地 thay cho 得 trong cấu trúc này.'),
 gi('G2-10','Bổ ngữ kết quả cơ bản','V + 完/好/到/见','Cho biết kết quả đạt được sau hành động.','我看完这本书了。','Wǒ kànwán zhè běn shū le.','Tôi đã đọc xong cuốn sách này.','Không tách bổ ngữ kết quả khỏi động từ nếu không có cấu trúc đặc biệt.'),
 gi('G2-11','Thời lượng hành động','V + thời lượng','Nói hành động kéo dài bao lâu.','我学了两年中文。','Wǒ xué le liǎng nián Zhōngwén.','Tôi đã học tiếng Trung hai năm.','Với tân ngữ là đại từ/người, vị trí thời lượng cần điều chỉnh theo mẫu.'),
 gi('G2-12','Tần suất với 次','V + số + 次','Cho biết hành động xảy ra bao nhiêu lần.','我看过两次。','Wǒ kànguo liǎng cì.','Tôi đã xem hai lần.','次 đếm số lần, không thay cho thời lượng.'),
 gi('G2-13','Vừa… vừa…','一边…一边…','Hai hành động diễn ra đồng thời bởi cùng một chủ thể.','她一边听音乐，一边学习。','Tā yìbiān tīng yīnyuè, yìbiān xuéxí.','Cô ấy vừa nghe nhạc vừa học.','Không dùng khi hai hành động không thể diễn ra đồng thời.'),
 gi('G2-14','Trình tự trước–sau','先…然后/再…','Sắp xếp hai hoặc nhiều hành động theo thứ tự.','我先吃饭，然后去上班。','Wǒ xiān chīfàn, ránhòu qù shàngbān.','Tôi ăn cơm trước rồi đi làm.','再 trong mẫu này chỉ hành động tiếp theo, không phải “lại” đã xảy ra.'),
 gi('G2-15','Nguyên nhân–kết quả','因为…所以…','Nêu nguyên nhân và kết quả rõ ràng.','因为下雨，所以我没去。','Yīnwèi xiàyǔ, suǒyǐ wǒ méi qù.','Vì trời mưa nên tôi không đi.','Trong hội thoại có thể lược một vế, nhưng bài học nên nhận diện đủ cặp.'),
 gi('G2-16','Nhượng bộ cơ bản','虽然…但是…','Vế đầu thừa nhận tình huống, vế sau nêu kết quả trái kỳ vọng.','虽然很累，但是他还在工作。','Suīrán hěn lèi, dànshì tā hái zài gōngzuò.','Tuy rất mệt nhưng anh ấy vẫn làm việc.','Không dùng 所以 ở vế sau của mẫu nhượng bộ.'),
 gi('G2-17','Lựa chọn trong câu hỏi','A 还是 B？','Dùng 还是 để hỏi lựa chọn giữa hai khả năng.','你喝茶还是咖啡？','Nǐ hē chá háishi kāfēi?','Bạn uống trà hay cà phê?','Trong câu trần thuật lựa chọn thường dùng 或者.'),
 gi('G2-18','Hoặc trong câu trần thuật','A 或者 B','Nối các khả năng hoặc lựa chọn trong câu kể.','周末我看书或者运动。','Zhōumò wǒ kànshū huòzhě yùndòng.','Cuối tuần tôi đọc sách hoặc tập thể dục.','Không dùng 或者 thay 还是 trong câu hỏi lựa chọn trực tiếp.'),
 gi('G2-19','Xin phép với 可以','可以 + V + 吗？','Hỏi hoặc cho phép thực hiện hành động.','我可以进来吗？','Wǒ kěyǐ jìnlái ma?','Tôi có thể vào không?','Phân biệt 可以 về điều kiện/cho phép với 会 về kỹ năng.'),
 gi('G2-20','Khả năng kỹ năng với 会','会 + V','Nói kỹ năng đã học hoặc khả năng dự đoán.','我会开车。','Wǒ huì kāichē.','Tôi biết lái xe.','Không dùng 会 cho điều kiện khách quan khi 能 phù hợp hơn.'),
 gi('G2-21','Khả năng điều kiện với 能','能 + V','Nói khả năng dựa trên sức lực, điều kiện hoặc hoàn cảnh.','今天我不能来。','Jīntiān wǒ bù néng lái.','Hôm nay tôi không thể đến.','Không dùng 不会 nếu ý là điều kiện không cho phép.'),
 gi('G2-22','Làm lại trong tương lai với 再','再 + V','Hành động sẽ lặp lại hoặc tiếp tục sau thời điểm nói.','请再说一遍。','Qǐng zài shuō yí biàn.','Xin nói lại một lần nữa.','Việc đã lặp lại trong quá khứ thường dùng 又.'),
 gi('G2-23','Lại xảy ra với 又','又 + V/Adj','Hành động hoặc tình trạng đã lặp lại, thường là điều đã xảy ra.','他昨天又迟到了。','Tā zuótiān yòu chídào le.','Hôm qua anh ấy lại đến muộn.','Không dùng 又 cho lời yêu cầu làm lại trong tương lai.'),
 gi('G2-24','Câu sai khiến với 让','A + 让 + B + V','A bảo, cho phép hoặc khiến B làm gì.','老师让我们读课文。','Lǎoshī ràng wǒmen dú kèwén.','Giáo viên bảo chúng tôi đọc bài khóa.','Xác định rõ người ra tác động và người thực hiện hành động.'),
 gi('G2-25','Câu tồn hiện với 有','Nơi chốn + 有 + người/vật','Giới thiệu sự tồn tại của người/vật tại một nơi.','桌子上有一本书。','Zhuōzi shàng yǒu yì běn shū.','Trên bàn có một cuốn sách.','Không dùng 是 để thay 有 khi mục đích là giới thiệu sự tồn tại.'),
],
3: [
 gi('G3-01','Câu chữ 把','S + 把 + O + V + kết quả','Nhấn mạnh việc xử lý một tân ngữ xác định và kết quả của hành động.','请把门关上。','Qǐng bǎ mén guānshang.','Hãy đóng cửa lại.','Sau động từ thường cần kết quả, phương hướng, số lượng hoặc thành phần bổ sung.'),
 gi('G3-02','Câu bị động với 被','O + 被 + S + V','Nhấn mạnh đối tượng chịu tác động; tác nhân có thể lược.','我的手机被他拿走了。','Wǒ de shǒujī bèi tā názǒu le.','Điện thoại của tôi bị anh ấy mang đi.','Không phải mọi câu bị động tiếng Việt đều cần dùng 被 trong tiếng Trung.'),
 gi('G3-03','Bổ ngữ khả năng','V + 得/不 + kết quả','Cho biết hành động có thể hoặc không thể đạt kết quả.','这本书我看得懂。','Zhè běn shū wǒ kàn de dǒng.','Cuốn sách này tôi đọc hiểu được.','Phân biệt 看不懂 với 没看懂: không thể hiểu và đã không hiểu.'),
 gi('G3-04','Bổ ngữ phương hướng đơn','V + 来/去','Cho biết hành động hướng về hoặc rời xa người nói/điểm quy chiếu.','请进来坐。','Qǐng jìnlái zuò.','Mời vào ngồi.','Chọn 来/去 theo điểm nhìn, không chỉ theo nghĩa tiếng Việt.'),
 gi('G3-05','Bổ ngữ phương hướng kép','V + 上/下/进/出/回/过/起 + 来/去','Diễn tả hướng chuyển động chi tiết.','他跑上楼去了。','Tā pǎoshàng lóu qù le.','Anh ấy chạy lên lầu.','Tân ngữ địa điểm có vị trí riêng giữa các thành phần phương hướng.'),
 gi('G3-06','Càng ngày càng','越来越 + Adj/V','Mức độ tăng dần theo thời gian.','天气越来越热了。','Tiānqì yuèláiyuè rè le.','Thời tiết ngày càng nóng.','Không thêm 更 ngay trước tính từ trong cùng cấu trúc.'),
 gi('G3-07','Càng A càng B','越 A 越 B','Mức độ B thay đổi theo mức độ A.','你越练习，说得越好。','Nǐ yuè liànxí, shuō de yuè hǎo.','Bạn càng luyện thì nói càng tốt.','Hai vế phải có quan hệ biến đổi tương ứng.'),
 gi('G3-08','Vừa… đã…','一…就…','Vế sau xảy ra ngay khi vế trước hoàn thành/xuất hiện.','我一到家就给你打电话。','Wǒ yí dào jiā jiù gěi nǐ dǎ diànhuà.','Tôi vừa về đến nhà là gọi cho bạn.','Chú ý biến điệu 一 trong lời nói.'),
 gi('G3-09','Ngoài… còn…','除了…以外，还/也…','Bổ sung thông tin ngoài đối tượng đã nêu.','除了中文以外，他还会英语。','Chúle Zhōngwén yǐwài, tā hái huì Yīngyǔ.','Ngoài tiếng Trung, anh ấy còn biết tiếng Anh.','Nếu biểu thị ngoại lệ toàn bộ, vế sau thường dùng 都.'),
 gi('G3-10','Không những… mà còn…','不但…而且…','Tăng tiến từ thông tin thứ nhất sang thông tin thứ hai.','她不但聪明，而且很努力。','Tā búdàn cōngming, érqiě hěn nǔlì.','Cô ấy không những thông minh mà còn rất chăm chỉ.','Hai vế nên cùng chủ ngữ hoặc bố trí chủ ngữ nhất quán.'),
 gi('G3-11','Chỉ cần… thì…','只要…就…','Nêu điều kiện đủ để kết quả xảy ra.','只要努力，就会进步。','Zhǐyào nǔlì, jiù huì jìnbù.','Chỉ cần cố gắng thì sẽ tiến bộ.','Không nhầm với 只有…才… là điều kiện cần/duy nhất.'),
 gi('G3-12','Chỉ có… mới…','只有…才…','Nêu điều kiện cần hoặc con đường duy nhất dẫn đến kết quả.','只有多练习，才能说得好。','Zhǐyǒu duō liànxí, cái néng shuō de hǎo.','Chỉ có luyện nhiều mới nói tốt được.','Không thay 才 bằng 就 nếu muốn nhấn mạnh điều kiện bắt buộc.'),
 gi('G3-13','Nếu… thì…','如果…就…','Nêu điều kiện giả định và kết quả.','如果明天下雨，我们就不去。','Rúguǒ míngtiān xiàyǔ, wǒmen jiù bú qù.','Nếu mai mưa thì chúng tôi không đi.','Có thể lược 如果 hoặc 就 trong hội thoại nhưng cần giữ logic điều kiện.'),
 gi('G3-14','Cho dù… vẫn…','即使…也…','Nêu giả định nhượng bộ: kết quả không thay đổi dù điều kiện xảy ra.','即使很忙，他也会来。','Jíshǐ hěn máng, tā yě huì lái.','Dù rất bận anh ấy vẫn sẽ đến.','Không dùng 所以 ở vế kết quả.'),
 gi('G3-15','Vừa mới với 刚/刚才','刚 + V; 刚才 + mệnh đề','刚 là phó từ chỉ hành động vừa xảy ra; 刚才 là danh từ thời gian.','我刚吃完饭。','Wǒ gāng chīwán fàn.','Tôi vừa ăn cơm xong.','刚才 có thể đứng đầu câu; 刚 thường đứng sát động từ.'),
 gi('G3-16','Muộn/mới với 才','thời gian/số lượng + 才 + V','Nhấn mạnh sự việc xảy ra muộn, ít hoặc khó hơn kỳ vọng.','他十点才到。','Tā shí diǎn cái dào.','Mười giờ anh ấy mới đến.','Sắc thái trái với 就: 才 muộn/khó, 就 sớm/dễ.'),
 gi('G3-17','Sớm/ngay với 就','thời gian/điều kiện + 就 + V','Nhấn mạnh xảy ra sớm, nhanh hoặc ngay khi có điều kiện.','他八点就到了。','Tā bā diǎn jiù dào le.','Tám giờ anh ấy đã đến rồi.','Không dịch máy móc 就 luôn là “thì”.'),
 gi('G3-18','Dù thế nào với 不管','不管…都/也…','Kết quả không thay đổi trước nhiều điều kiện khác nhau.','不管多忙，他都坚持学习。','Bùguǎn duō máng, tā dōu jiānchí xuéxí.','Dù bận thế nào anh ấy cũng kiên trì học.','Vế sau thường cần 都 hoặc 也.'),
 gi('G3-19','Mục đích với 为了','为了 + mục đích，S + V','Nêu mục đích của hành động ở vế chính.','为了身体健康，他每天跑步。','Wèile shēntǐ jiànkāng, tā měitiān pǎobù.','Vì sức khỏe, anh ấy chạy mỗi ngày.','Phân biệt 为了 nêu mục đích với 因为 nêu nguyên nhân.'),
 gi('G3-20','Theo/đối với với 对','S + 对 + O + V/Adj','Nêu đối tượng của thái độ, hành vi hoặc đánh giá.','老师对我们很耐心。','Lǎoshī duì wǒmen hěn nàixīn.','Giáo viên rất kiên nhẫn với chúng tôi.','Không đặt 对 sau động từ nếu nó đang dẫn đối tượng của cả cụm.'),
 gi('G3-21','Ngay cả… cũng…','连…都/也…','Nhấn mạnh một trường hợp cực đoan hoặc bất ngờ.','他忙得连饭都没吃。','Tā máng de lián fàn dōu méi chī.','Anh ấy bận đến mức cơm cũng chưa ăn.','Phải có 都/也 để hoàn chỉnh sắc thái nhấn mạnh.'),
 gi('G3-22','Mức độ đến nỗi','Adj/V + 得 + mệnh đề','Bổ ngữ mức độ dẫn đến một kết quả hoặc trạng thái cụ thể.','孩子高兴得跳了起来。','Háizi gāoxìng de tiào le qǐlái.','Đứa trẻ vui đến mức nhảy lên.','Phân biệt 得 nối bổ ngữ với 地 nối trạng ngữ.'),
 gi('G3-23','Gần như với 差点儿','差点儿 + V','Nói một việc suýt xảy ra hoặc suýt không đạt được.','我差点儿迟到。','Wǒ chàdiǎnr chídào.','Tôi suýt đến muộn.','Cần dựa vào ngữ cảnh để hiểu kết quả thực tế có xảy ra hay không.'),
 gi('G3-24','Tiếp tục với 继续','继续 + V/O','Hành động được tiếp tục sau một khoảng dừng hoặc trạng thái trước đó.','休息以后，我们继续工作。','Xiūxi yǐhòu, wǒmen jìxù gōngzuò.','Sau khi nghỉ, chúng tôi tiếp tục làm việc.','Không nhầm với 一直 là liên tục không ngắt.'),
 gi('G3-25','Liên tục với 一直','一直 + V/Adj','Diễn tả trạng thái/hành động kéo dài liên tục trong một khoảng.','我一直住在这里。','Wǒ yìzhí zhù zài zhèlǐ.','Tôi luôn sống ở đây.','Không nhất thiết mang nghĩa “mãi mãi”; cần giới hạn thời gian theo ngữ cảnh.'),
 gi('G3-26','Ngày nào cũng/cứ mỗi','每 + N + 都…','Nói quy luật áp dụng cho từng thành viên/thời điểm.','我每天都复习生词。','Wǒ měitiān dōu fùxí shēngcí.','Ngày nào tôi cũng ôn từ mới.','Vế sau thường cần 都 để bao quát.'),
 gi('G3-27','Động tác thử/nhẹ với 一下','V + 一下','Làm hành động ngắn, thử hoặc làm yêu cầu mềm hơn.','你看一下这个问题。','Nǐ kàn yíxià zhège wèntí.','Bạn xem thử vấn đề này.','Không dùng với động từ trạng thái không phù hợp.'),
 gi('G3-28','Lặp động từ','AA / A一A / ABAB','Biểu thị hành động ngắn, thử hoặc nhẹ nhàng.','我们一起讨论讨论吧。','Wǒmen yìqǐ tǎolun tǎolun ba.','Chúng ta cùng thảo luận một chút nhé.','Không lặp tùy tiện mọi động từ; động từ hai âm tiết thường dùng ABAB.'),
 gi('G3-29','Ước lượng số lượng','số + 多/左右','Nói số lượng hơn một chút hoặc xấp xỉ.','会议开了两个多小时。','Huìyì kāi le liǎng ge duō xiǎoshí.','Cuộc họp kéo dài hơn hai giờ.','Vị trí 多 phụ thuộc đơn vị số lượng.'),
 gi('G3-30','Câu phản vấn với 不是…吗','不是…吗？','Dùng để nhắc lại điều người nói cho là đã rõ hoặc bày tỏ ngạc nhiên.','你不是说今天来吗？','Nǐ bú shì shuō jīntiān lái ma?','Chẳng phải bạn nói hôm nay đến sao?','Sắc thái có thể mạnh; tránh dùng trong tình huống cần quá lịch sự.'),
],
4: [
 gi('G4-01','Bất luận với 无论','无论…都/也…','Nêu nhiều điều kiện nhưng kết quả vẫn không thay đổi.','无论遇到什么困难，他都不放弃。','Wúlùn yùdào shénme kùnnan, tā dōu bù fàngqì.','Bất luận gặp khó khăn gì anh ấy cũng không bỏ cuộc.','Vế sau thường cần 都 hoặc 也.'),
 gi('G4-02','Mặc dù với 尽管','尽管…但是/可是…','Thừa nhận sự thật ở vế đầu và nêu kết quả trái kỳ vọng ở vế sau.','尽管天气不好，我们还是出发了。','Jǐnguǎn tiānqì bù hǎo, wǒmen háishi chūfā le.','Mặc dù thời tiết xấu, chúng tôi vẫn xuất phát.','Không nhầm 尽管 nhượng bộ với 尽量 nghĩa là cố gắng hết mức.'),
 gi('G4-03','Bởi vì theo văn viết','由于…因此/所以…','Nêu nguyên nhân và kết quả theo sắc thái trang trọng hơn 因为.','由于准备充分，比赛进行得很顺利。','Yóuyú zhǔnbèi chōngfèn, bǐsài jìnxíng de hěn shùnlì.','Do chuẩn bị đầy đủ, cuộc thi diễn ra thuận lợi.','Tránh dùng quá dày trong hội thoại thân mật.'),
 gi('G4-04','Đối với với 对于','对于 + O，S + nhận xét','Đưa đối tượng được bàn luận lên đầu câu.','对于这个问题，大家有不同的看法。','Duìyú zhège wèntí, dàjiā yǒu bùtóng de kànfǎ.','Đối với vấn đề này, mọi người có ý kiến khác nhau.','Phân biệt với 关于 giới thiệu chủ đề hơn là thái độ/tác động.'),
 gi('G4-05','Về chủ đề với 关于','关于 + chủ đề + 的 + N','Giới thiệu nội dung hoặc chủ đề liên quan.','我看了一本关于中国文化的书。','Wǒ kàn le yì běn guānyú Zhōngguó wénhuà de shū.','Tôi đọc một cuốn sách về văn hóa Trung Quốc.','Không dùng 关于 để thay 对于 trong mọi trường hợp.'),
 gi('G4-06','Theo căn cứ với 按照','按照 + quy tắc/cách thức + V','Thực hiện hành động dựa trên tiêu chuẩn hoặc chỉ dẫn.','请按照说明操作。','Qǐng ànzhào shuōmíng cāozuò.','Hãy thao tác theo hướng dẫn.','Sau 按照 cần căn cứ rõ ràng, không phải người nhận hành động.'),
 gi('G4-07','Thông qua với 通过','通过 + phương thức + V','Nêu phương tiện/cách thức đạt mục tiêu.','通过练习，他的口语提高了。','Tōngguò liànxí, tā de kǒuyǔ tígāo le.','Thông qua luyện tập, khẩu ngữ của anh ấy đã tiến bộ.','Phân biệt nghĩa phương thức với nghĩa đi xuyên qua địa điểm.'),
 gi('G4-08','Không phải… mà là…','不是…而是…','Sửa lại hoặc đối lập hai phán đoán.','问题不是没有时间，而是没有计划。','Wèntí bú shì méiyǒu shíjiān, érshì méiyǒu jìhuà.','Vấn đề không phải không có thời gian mà là không có kế hoạch.','Hai vế nên cùng cấp ngữ pháp để đối chiếu rõ.'),
 gi('G4-09','Một mặt… mặt khác…','一方面…另一方面…','Trình bày hai phương diện song song của vấn đề.','一方面要提高速度，另一方面要保证质量。','Yì fāngmiàn yào tígāo sùdù, lìng yì fāngmiàn yào bǎozhèng zhìliàng.','Một mặt phải tăng tốc độ, mặt khác phải bảo đảm chất lượng.','Không nhất thiết hai phương diện đối lập; có thể bổ sung nhau.'),
 gi('G4-10','Nếu đã… thì…','既然…就…','Dựa trên sự thật đã xác định để đưa ra kết luận hoặc đề nghị.','既然决定了，就认真去做吧。','Jìrán juédìng le, jiù rènzhēn qù zuò ba.','Đã quyết định rồi thì hãy làm nghiêm túc.','既然 không dùng cho điều kiện chưa chắc xảy ra như 如果.'),
 gi('G4-11','Không những… thậm chí…','不但…甚至…','Đưa thông tin tăng tiến đến mức bất ngờ hơn.','他不但会说中文，甚至会写毛笔字。','Tā búdàn huì shuō Zhōngwén, shènzhì huì xiě máobǐzì.','Anh ấy không chỉ nói được tiếng Trung mà thậm chí còn viết thư pháp.','甚至 phải dẫn phần cao hơn về mức độ hoặc bất ngờ.'),
 gi('G4-12','Thậm chí với 甚至','…，甚至…','Nhấn mạnh trường hợp cực đoan hoặc cao hơn thông tin trước.','天气很冷，甚至开始下雪了。','Tiānqì hěn lěng, shènzhì kāishǐ xiàxuě le.','Trời rất lạnh, thậm chí bắt đầu có tuyết.','Không dùng nếu phần sau không mạnh hơn phần trước.'),
 gi('G4-13','Ngược lại với 反而','…，反而…','Kết quả trái với dự đoán hoặc trái với điều vừa nêu.','休息以后，他反而更累了。','Xiūxi yǐhòu, tā fǎn’ér gèng lèi le.','Sau khi nghỉ anh ấy ngược lại còn mệt hơn.','Cần có nền kỳ vọng rõ để 反而 có ý nghĩa.'),
 gi('G4-14','Hơn nữa với 而且','mệnh đề，而且 + mệnh đề','Bổ sung thông tin cùng hướng, thường tăng mức độ.','这家饭店环境好，而且服务也很周到。','Zhè jiā fàndiàn huánjìng hǎo, érqiě fúwù yě hěn zhōudào.','Nhà hàng này môi trường tốt, hơn nữa phục vụ chu đáo.','Không dùng 而且 để biểu thị đối lập.'),
 gi('G4-15','Tuy nhiên với 然而','mệnh đề，然而 + mệnh đề','Nối ý đối lập theo phong cách văn viết.','计划很完整，然而执行起来并不容易。','Jìhuà hěn wánzhěng, rán’ér zhíxíng qǐlái bìng bù róngyì.','Kế hoạch đầy đủ, tuy nhiên thực hiện không dễ.','Trong hội thoại thường dùng 但是/可是 tự nhiên hơn.'),
 gi('G4-16','Thật ra với 其实','其实 + mệnh đề','Đưa ra sự thật bổ sung, sửa hiểu lầm hoặc quan điểm thật.','其实这个问题没有那么复杂。','Qíshí zhège wèntí méiyǒu nàme fùzá.','Thật ra vấn đề này không phức tạp đến vậy.','Không nhầm 其实 với 的确 là xác nhận mạnh.'),
 gi('G4-17','Vốn dĩ với 本来','本来 + tình trạng，后来/可是…','Nói tình trạng hoặc ý định ban đầu trước khi thay đổi.','我本来想去，可是临时有事。','Wǒ běnlái xiǎng qù, kěshì línshí yǒu shì.','Ban đầu tôi định đi nhưng đột xuất có việc.','Phân biệt với 原来 khi “hóa ra” sau khi phát hiện.'),
 gi('G4-18','Hóa ra với 原来','原来 + phát hiện/sự thật','Biểu thị người nói vừa phát hiện hoặc hiểu ra tình hình.','原来你们早就认识。','Yuánlái nǐmen zǎojiù rènshi.','Hóa ra các bạn đã quen nhau từ lâu.','原来 còn có nghĩa “ban đầu”; cần dựa ngữ cảnh.'),
 gi('G4-19','Trước hết với 首先','首先…其次/然后…','Tổ chức trình tự lập luận hoặc hành động rõ ràng.','首先要了解情况，然后再作决定。','Shǒuxiān yào liǎojiě qíngkuàng, ránhòu zài zuò juédìng.','Trước hết phải hiểu tình hình rồi mới quyết định.','Không lạm dụng 首先 nếu chỉ có một hành động.'),
 gi('G4-20','Cuối cùng với 最后','…，最后…','Nêu bước cuối hoặc kết quả cuối cùng.','我们讨论了很久，最后同意了这个办法。','Wǒmen tǎolùn le hěn jiǔ, zuìhòu tóngyì le zhège bànfǎ.','Chúng tôi thảo luận lâu và cuối cùng đồng ý cách này.','Phân biệt 最后 với 终于: 终于 nhấn mạnh sau chờ đợi/khó khăn.'),
 gi('G4-21','Rốt cuộc với 终于','S + 终于 + V','Kết quả đạt được sau thời gian, nỗ lực hoặc khó khăn.','经过努力，他终于成功了。','Jīngguò nǔlì, tā zhōngyú chénggōng le.','Sau nỗ lực, cuối cùng anh ấy đã thành công.','Không dùng cho một bước cuối trung tính nếu không có sắc thái chờ đợi.'),
 gi('G4-22','Kết quả bất ngờ với 居然','S + 居然 + V/Adj','Biểu thị kết quả ngoài dự đoán.','这么难的题，他居然答对了。','Zhème nán de tí, tā jūrán dáduì le.','Câu khó như vậy mà anh ấy lại trả lời đúng.','居然 mang thái độ ngạc nhiên của người nói.'),
 gi('G4-23','Có lẽ với 恐怕','恐怕 + mệnh đề','Nêu dự đoán lo ngại hoặc cách nói giảm nhẹ.','今天恐怕不能按时完成。','Jīntiān kǒngpà bù néng ànshí wánchéng.','Hôm nay e rằng không thể hoàn thành đúng giờ.','Không nhất thiết luôn mang nghĩa sợ hãi trực tiếp.'),
 gi('G4-24','Chắc chắn với 肯定','肯定 + V/Adj; 肯定是…','Biểu thị sự xác nhận hoặc dự đoán chắc chắn.','他准备得这么充分，肯定没问题。','Tā zhǔnbèi de zhème chōngfèn, kěndìng méi wèntí.','Anh ấy chuẩn bị kỹ vậy chắc chắn không vấn đề.','Phân biệt với 一定 có thể dùng cả yêu cầu “nhất định phải”.'),
 gi('G4-25','Không hẳn với 不一定','不一定 + V/Adj','Phủ định tính chắc chắn, không đồng nghĩa với chắc chắn không.','贵的东西不一定适合你。','Guì de dōngxi bù yídìng shìhé nǐ.','Đồ đắt chưa chắc phù hợp với bạn.','Không dịch thành “nhất định không”; đó là 一定不.'),
 gi('G4-26','Gần như với 几乎','几乎 + V/Adj/数量','Nói mức độ rất gần hoàn toàn nhưng thường chưa tuyệt đối.','我几乎忘了这件事。','Wǒ jīhū wàng le zhè jiàn shì.','Tôi gần như quên việc này.','Khi kết quả thực tế quan trọng, cần nhìn 了/没 và ngữ cảnh.'),
 gi('G4-27','Hoàn toàn với 完全','完全 + V/Adj','Nhấn mạnh mức độ đầy đủ, không có ngoại lệ.','我完全同意你的意见。','Wǒ wánquán tóngyì nǐ de yìjiàn.','Tôi hoàn toàn đồng ý với ý kiến của bạn.','Không dùng quá mức khi chỉ muốn nói 很.'),
 gi('G4-28','Đặc biệt với 尤其','…，尤其是…','Làm nổi bật một thành phần trong nhóm.','我喜欢运动，尤其是游泳。','Wǒ xǐhuan yùndòng, yóuqí shì yóuyǒng.','Tôi thích thể thao, đặc biệt là bơi.','尤其是 thường dẫn ví dụ nổi bật, không phải nguyên nhân.'),
 gi('G4-29','Ví dụ với 例如','khái quát，例如 + ví dụ','Đưa ví dụ minh họa theo sắc thái tương đối trang trọng.','很多运动有利于健康，例如游泳和跑步。','Hěn duō yùndòng yǒulì yú jiànkāng, lìrú yóuyǒng hé pǎobù.','Nhiều môn thể thao tốt cho sức khỏe, ví dụ bơi và chạy.','Ví dụ phải thuộc phạm vi khái quát trước đó.'),
 gi('G4-30','Dần dần với 逐渐','S + 逐渐 + V/Adj','Sự thay đổi diễn ra từng bước theo thời gian.','他的中文水平逐渐提高了。','Tā de Zhōngwén shuǐpíng zhújiàn tígāo le.','Trình độ tiếng Trung của anh ấy dần nâng cao.','Khác 突然 là thay đổi đột ngột.'),
 gi('G4-31','Đồng thời với 同时','mệnh đề，同时 + mệnh đề','Hai hành động/tác dụng cùng tồn tại hoặc cùng thời gian.','这份工作能增加收入，同时也能积累经验。','Zhè fèn gōngzuò néng zēngjiā shōurù, tóngshí yě néng jīlěi jīngyàn.','Công việc này vừa tăng thu nhập vừa tích lũy kinh nghiệm.','Chủ ngữ và quan hệ hai vế cần rõ.'),
 gi('G4-32','Kịp thời với 及时','及时 + V','Hành động được thực hiện đúng lúc trước khi quá muộn.','发现问题以后要及时处理。','Fāxiàn wèntí yǐhòu yào jíshí chǔlǐ.','Sau khi phát hiện vấn đề phải xử lý kịp thời.','Phân biệt 及时 “kịp thời” với 按时 “đúng giờ đã định”.'),
 gi('G4-33','Đúng giờ với 按时','按时 + V','Thực hiện theo thời điểm hoặc lịch đã định.','请按时参加会议。','Qǐng ànshí cānjiā huìyì.','Hãy tham gia cuộc họp đúng giờ.','Không đồng nhất với 及时 là đúng thời điểm cần thiết.'),
 gi('G4-34','Đáng để với 值得','值得 + V','Nói điều gì xứng đáng để làm hoặc xem xét.','这本书值得认真读。','Zhè běn shū zhíde rènzhēn dú.','Cuốn sách này đáng đọc kỹ.','Sau 值得 thường là động từ/cụm động từ, không thêm 得 lần nữa.'),
 gi('G4-35','Có lợi cho với 对…有利','A 对 B 有利/有害','Nêu tác động có lợi hoặc có hại đến đối tượng.','运动对身体健康有利。','Yùndòng duì shēntǐ jiànkāng yǒulì.','Vận động có lợi cho sức khỏe.','Đặt 对 tượng tác động trước 有利/有害.'),
 gi('G4-36','Liên quan với 与…有关','A 与 B 有关','Nêu mối liên hệ giữa hai sự vật.','这个结果与准备是否充分有关。','Zhège jiéguǒ yǔ zhǔnbèi shìfǒu chōngfèn yǒuguān.','Kết quả này liên quan đến việc chuẩn bị đầy đủ hay không.','与 trang trọng hơn 和; 有关 không nhất thiết là quan hệ nhân quả.'),
 gi('G4-37','Dựa vào với 根据','根据 + căn cứ + phán đoán','Đưa ra kết luận dựa trên thông tin, quy định hoặc bằng chứng.','根据调查结果，我们改变了计划。','Gēnjù diàochá jiéguǒ, wǒmen gǎibiàn le jìhuà.','Dựa trên kết quả khảo sát, chúng tôi thay đổi kế hoạch.','Phân biệt 根据 nêu căn cứ với 按照 nêu cách thực hiện.'),
 gi('G4-38','Đối mặt với 面对','面对 + vấn đề/tình huống','Nói chủ thể trực tiếp gặp và xử lý tình huống.','面对困难，我们应该保持冷静。','Miànduì kùnnan, wǒmen yīnggāi bǎochí lěngjìng.','Đối mặt khó khăn, chúng ta nên bình tĩnh.','面对 là động từ/giới từ hóa; không dùng 对面 thay thế.'),
 gi('G4-39','Tránh với 避免','避免 + N/V','Ngăn một tình huống không mong muốn xảy ra.','提前准备可以避免很多麻烦。','Tíqián zhǔnbèi kěyǐ bìmiǎn hěn duō máfan.','Chuẩn bị trước có thể tránh nhiều phiền phức.','Sau 避免 thường là điều tiêu cực cần ngăn.'),
 gi('G4-40','Dẫn đến với 导致','nguyên nhân + 导致 + kết quả','Nêu quan hệ nguyên nhân gây ra kết quả, thường tiêu cực.','缺少沟通容易导致误会。','Quēshǎo gōutōng róngyì dǎozhì wùhuì.','Thiếu giao tiếp dễ dẫn đến hiểu lầm.','Không dùng cho mọi kết quả trung tính nếu 造成/使 phù hợp hơn.'),
 gi('G4-41','Khiến cho với 使','A + 使 + B + V/Adj','A làm cho B có hành động hoặc trạng thái.','这次经历使我更有信心。','Zhè cì jīnglì shǐ wǒ gèng yǒu xìnxīn.','Trải nghiệm này khiến tôi tự tin hơn.','使 trang trọng hơn 让; tránh lặp chủ ngữ mơ hồ.'),
 gi('G4-42','Nói chung với 总的来说','总的来说，mệnh đề','Tóm tắt đánh giá chung sau khi phân tích nhiều mặt.','总的来说，这个计划是可行的。','Zǒng de lái shuō, zhège jìhuà shì kěxíng de.','Nói chung, kế hoạch này khả thi.','Dùng ở phần tổng kết, không thay cho mọi câu mở đầu.'),
]
}


def write_grammar(level: int, items: list[dict]):
    payload = {
        'meta': {
            'level': str(level), 'version': '4.0.0', 'itemCount': len(items),
            'description': f'Các cấu trúc ngữ pháp trọng tâm HSK {level}, có công thức, giải thích, ví dụ và lỗi thường gặp.'
        },
        'items': items
    }
    (ROOT / f'data/hsk{level}-grammar.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    for level in LEVELS:
        pack = make_pack(level)
        (ROOT / f'data/hsk{level}-quality.json').write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding='utf-8')
        write_grammar(level, GRAMMAR[level])
        print(f'HSK {level}: {len(pack["words"])} từ, {len(GRAMMAR[level])} điểm ngữ pháp')
