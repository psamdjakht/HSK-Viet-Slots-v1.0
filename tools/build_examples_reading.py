#!/usr/bin/env python3
from __future__ import annotations
import json, re
from pathlib import Path
from pypinyin import lazy_pinyin, Style

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
READING_DIR = DATA / 'reading'
READING_DIR.mkdir(parents=True, exist_ok=True)


def sentence_pinyin(text: str) -> str:
    parts = lazy_pinyin(text, style=Style.TONE, neutral_tone_with_five=False, errors=lambda x: list(x))
    out = ' '.join(parts)
    out = re.sub(r'\s+([，。！？；：、“”‘’（）])', r'\1', out)
    out = re.sub(r'([“‘（])\s+', r'\1', out)
    return out[:1].upper() + out[1:] if out else ''


def han_count(text: str) -> int:
    return len(re.findall(r'[\u3400-\u9fff]', text))


def controlled_examples(word: dict, pack: dict, level: int) -> list[dict]:
    target = word['simplified']
    meaning = pack.get('primaryMeaning') or word.get('meaning') or 'nghĩa đang học'
    pos = pack.get('pos') or []
    topic = pack.get('topic') or 'từ vựng tổng hợp'
    base = pack.get('example') or word.get('example') or {}
    rows: list[dict] = []

    if base.get('zh') and base.get('kind') == 'usage':
        rows.append({
            'id': f"SE-{word['id']}-01",
            'zh': base['zh'],
            'pinyin': base.get('pinyin') or sentence_pinyin(base['zh']),
            'vi': base.get('vi') or '',
            'difficulty': level,
            'kind': 'usage',
            'status': base.get('status', 'bien_soan_he_thong'),
            'exerciseEligible': bool(base.get('exerciseEligible')),
            'note': 'Câu ngữ cảnh chính của từ.'
        })

    # Các mẫu có dấu ngoặc kép luôn đúng ngữ pháp, tránh gán sai cấu trúc cho từ chức năng hoặc thuật ngữ hiếm.
    if 'động từ' in pos:
        zh2 = f'今天的课上，老师说明了“{target}”在句子里的用法。'
        vi2 = f'Trong bài học hôm nay, giáo viên giải thích cách dùng “{target}” trong câu.'
    elif 'danh từ' in pos:
        zh2 = f'课文里出现了“{target}”这个词，我们先了解它的基本意思。'
        vi2 = f'Từ “{target}” xuất hiện trong bài khóa; trước tiên chúng ta tìm hiểu nghĩa cơ bản của nó.'
    elif 'tính từ' in pos:
        zh2 = f'“{target}”常用来说明人、事物或情况的特点。'
        vi2 = f'“{target}” thường được dùng để miêu tả đặc điểm của người, sự vật hoặc tình huống.'
    elif 'lượng từ' in pos or 'số từ' in pos:
        zh2 = f'“{target}”在这个句子里和数量有关。'
        vi2 = f'“{target}” trong câu này có liên quan đến số lượng.'
    elif any(x in pos for x in ['trợ từ','giới từ','liên từ','phó từ','đại từ','tiền tố','hậu tố']):
        zh2 = f'学习“{target}”时，要注意它在句子中的位置和作用。'
        vi2 = f'Khi học “{target}”, cần chú ý vị trí và chức năng của nó trong câu.'
    else:
        zh2 = f'今天我们学习“{target}”，并在上下文中理解它的意思。'
        vi2 = f'Hôm nay chúng ta học “{target}” và hiểu nghĩa của nó trong ngữ cảnh.'

    rows.append({
        'id': f"SE-{word['id']}-{len(rows)+1:02d}",
        'zh': zh2,
        'pinyin': sentence_pinyin(zh2),
        'vi': vi2,
        'difficulty': level,
        'kind': 'guided_context',
        'status': 'mau_hoc_an_toan',
        'exerciseEligible': False,
        'note': f'Mẫu học an toàn theo từ loại và chủ đề {topic}; không dùng tạo đề.'
    })

    zh3 = f'请把“{target}”的常用意思一起记住，再自己造一个句子。'
    vi3 = f'Hãy ghi nhớ “{target}” cùng nghĩa “{meaning}”, sau đó tự đặt một câu.'
    rows.append({
        'id': f"SE-{word['id']}-{len(rows)+1:02d}",
        'zh': zh3,
        'pinyin': sentence_pinyin(zh3),
        'vi': vi3,
        'difficulty': min(7, level + 1),
        'kind': 'active_recall',
        'status': 'mau_hoc_an_toan',
        'exerciseEligible': False,
        'note': 'Mẫu gợi nhớ chủ động, không dùng tạo đề.'
    })

    # Mọi cấp có tối thiểu ba mục để cấu trúc câu ví dụ thống nhất.
    if len(rows) < 3:
        zh4 = f'读完例句以后，请说一说你在什么情况下会用“{target}”。'
        vi4 = f'Sau khi đọc câu ví dụ, hãy nói xem trong tình huống nào bạn sẽ dùng “{target}”.'
        rows.append({
            'id': f"SE-{word['id']}-{len(rows)+1:02d}",
            'zh': zh4,
            'pinyin': sentence_pinyin(zh4),
            'vi': vi4,
            'difficulty': min(7, level + 1),
            'kind': 'production_prompt',
            'status': 'mau_hoc_an_toan',
            'exerciseEligible': False,
            'note': 'Câu gợi ý luyện nói.'
        })
    return rows[:3]


def build_examples() -> None:
    output = {'meta': {'version':'6.0.0','description':'Cấu trúc câu ví dụ chuẩn hóa cho toàn bộ từ HSK 1–6 và HSK 7–9. Câu luyện tập chỉ lấy mục exerciseEligible.'}, 'words': {}}
    counts = {}
    for level in range(1,8):
        level_data = json.loads((DATA / 'levels' / f'hsk{level}.json').read_text(encoding='utf-8'))['words']
        quality = json.loads((DATA / f'hsk{level}-quality.json').read_text(encoding='utf-8'))['words']
        count = 0
        eligible = 0
        for word in level_data:
            rows = controlled_examples(word, quality.get(word['id'], {}), level)
            output['words'][word['id']] = rows
            count += len(rows)
            eligible += sum(1 for x in rows if x['exerciseEligible'])
        counts[str(level)] = {'words': len(level_data), 'examples': count, 'exerciseEligible': eligible}
    output['meta']['counts'] = counts
    (DATA / 'standardized-examples.json').write_text(json.dumps(output, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')



EXPANSION_BANKS = {
1: [
('回家以后，我也很开心。','Sau khi về nhà, tôi cũng rất vui.'),
('晚上我把今天的事告诉家人。','Buổi tối tôi kể chuyện hôm nay cho gia đình.'),
('明天我还想再去一次。','Ngày mai tôi vẫn muốn đi thêm một lần.'),
('这是很有意思的一天。','Đây là một ngày rất thú vị.'),
('我觉得今天过得很快。','Tôi thấy hôm nay trôi qua rất nhanh.')],
2: [
('晚上回家以后，我把今天的事情告诉了家人。','Buổi tối về nhà, tôi kể chuyện hôm nay cho gia đình.'),
('大家听了以后都觉得很有意思。','Mọi người nghe xong đều thấy rất thú vị.'),
('这次经历也让我学到了新的东西。','Trải nghiệm này cũng giúp tôi học được điều mới.'),
('我希望下次还能有这样的机会。','Tôi hy vọng lần sau vẫn có cơ hội như vậy.'),
('虽然过程不完全顺利，但是结果很好。','Dù quá trình không hoàn toàn thuận lợi, kết quả rất tốt.')],
3: [
('回家以后，我把这次经历写进了日记。','Sau khi về nhà, tôi ghi trải nghiệm này vào nhật ký.'),
('我也认真想了想自己做得好的地方和需要改进的地方。','Tôi cũng suy nghĩ nghiêm túc về điểm mình làm tốt và điểm cần cải thiện.'),
('以后遇到相似的情况时，我希望自己能够更冷静、更有耐心。','Sau này khi gặp tình huống tương tự, tôi hy vọng mình bình tĩnh và kiên nhẫn hơn.'),
('我还把自己的想法告诉了朋友，听取了他们的建议。','Tôi còn nói suy nghĩ với bạn và nghe lời khuyên của họ.'),
('通过交流，我发现每个人看问题的角度都不一样。','Qua trao đổi, tôi nhận ra mỗi người nhìn vấn đề từ góc độ khác nhau.')],
4: [
('后来，我又从网上查找了一些相关资料，也听取了不同人的意见。','Sau đó, tôi tìm thêm tài liệu liên quan trên mạng và lắng nghe ý kiến của nhiều người.'),
('这些信息让我发现，很多问题没有唯一的答案，而是需要根据具体情况进行判断。','Những thông tin này giúp tôi nhận ra nhiều vấn đề không có đáp án duy nhất mà cần phán đoán theo tình huống cụ thể.'),
('如果只看到事情的一面，就很容易得出过于简单的结论。','Nếu chỉ nhìn một mặt của sự việc, rất dễ đưa ra kết luận quá đơn giản.'),
('因此，在作出决定以前，我们应该了解事实、比较选择，也要考虑决定可能带来的长期影响。','Vì vậy, trước khi quyết định, chúng ta nên hiểu sự thật, so sánh lựa chọn và cân nhắc ảnh hưởng lâu dài.'),
('这种思考方式不一定能保证每次都做对，却能帮助我们更清楚地承担自己的选择。','Cách suy nghĩ này không bảo đảm lần nào cũng đúng nhưng giúp ta chịu trách nhiệm rõ ràng hơn với lựa chọn của mình.')],
5: [
('从更长远的角度看，一个办法是否成功，不能只用短期的数据来判断。','Từ góc nhìn dài hạn, một biện pháp có thành công hay không không thể chỉ đánh giá bằng dữ liệu ngắn hạn.'),
('我们还需要观察它对不同群体的影响，以及这些影响是否能够公平地被承担。','Chúng ta còn cần quan sát ảnh hưởng của nó với các nhóm khác nhau và liệu các ảnh hưởng đó có được gánh chịu công bằng hay không.'),
('在执行过程中，公开的信息和清楚的责任分工尤其重要。','Trong quá trình thực hiện, thông tin công khai và phân công trách nhiệm rõ ràng đặc biệt quan trọng.'),
('如果参与者不知道目标、标准和反馈渠道，再好的计划也可能因为误解而失去效果。','Nếu người tham gia không biết mục tiêu, tiêu chuẩn và kênh phản hồi, kế hoạch tốt đến đâu cũng có thể mất hiệu quả vì hiểu lầm.'),
('另一方面，规则也不能完全固定不变。','Mặt khác, quy tắc cũng không thể hoàn toàn cố định.'),
('当环境、技术或人们的需求发生变化时，管理者应该根据可靠的证据及时调整。','Khi môi trường, công nghệ hoặc nhu cầu thay đổi, người quản lý nên kịp thời điều chỉnh theo bằng chứng đáng tin.'),
('个人同样需要保留独立判断，而不是因为某种做法流行就直接接受。','Cá nhân cũng cần giữ phán đoán độc lập thay vì chấp nhận ngay chỉ vì một cách làm đang thịnh hành.'),
('通过记录实际结果、比较不同经验并持续讨论，我们才能逐步找到更合适的平衡。','Bằng cách ghi lại kết quả thực tế, so sánh kinh nghiệm và thảo luận liên tục, chúng ta mới dần tìm được sự cân bằng phù hợp hơn.'),
('真正有价值的改变通常不是一次完成的，而是在不断检查和修正中形成的。','Thay đổi thực sự có giá trị thường không hoàn thành trong một lần mà hình thành qua kiểm tra và sửa đổi liên tục.'),
('因此，面对复杂问题时，耐心、证据和合作往往比一个简单而响亮的答案更重要。','Vì vậy, khi đối mặt vấn đề phức tạp, kiên nhẫn, bằng chứng và hợp tác thường quan trọng hơn một câu trả lời đơn giản nhưng kêu vang.')],
}

def passage(level:int, slug:str, title:str, topic:str, sentences:list[tuple[str,str]], target:int) -> dict:
    sentences = list(sentences)
    bank = EXPANSION_BANKS[level]
    start = sum(ord(c) for c in slug) % len(bank)
    cursor = 0
    while han_count(''.join(zh for zh,_ in sentences)) < int(target * 0.9):
        pair = bank[(start + cursor) % len(bank)]
        if pair not in sentences:
            sentences.append(pair)
        cursor += 1
        if cursor > len(bank) * 2:
            break
    text = ''.join(zh for zh,_ in sentences)
    return {
        'id': f'READ-L{level}-{slug}',
        'level': str(level),
        'title': title,
        'topic': topic,
        'targetCharacters': target,
        'actualCharacters': han_count(text),
        'sentences': [
            {'id':f'READ-L{level}-{slug}-S{i+1:02d}','zh':zh,'pinyin':sentence_pinyin(zh),'vi':vi}
            for i,(zh,vi) in enumerate(sentences)
        ]
    }


PASSAGES = {
1: [
('morning','Buổi sáng của tôi','sinh hoạt',[
('我每天六点起床。','Mỗi ngày tôi thức dậy lúc sáu giờ.'),('我先喝水，再吃早饭。','Tôi uống nước trước, sau đó ăn sáng.'),('七点半，我坐车去学校。','Bảy giờ rưỡi, tôi đi xe đến trường.'),('老师和同学都很好。','Thầy cô và các bạn đều rất tốt.'),('我喜欢每天学习汉语。','Tôi thích học tiếng Trung mỗi ngày.')],50),
('family','Gia đình nhỏ','gia đình',[
('我家有四个人。','Gia đình tôi có bốn người.'),('爸爸在公司工作，妈妈是老师。','Bố làm việc ở công ty, mẹ là giáo viên.'),('我有一个妹妹，她五岁。','Tôi có một em gái, em ấy năm tuổi.'),('晚上我们一起吃饭，也一起说话。','Buổi tối chúng tôi cùng ăn cơm và trò chuyện.'),('我很爱我的家人。','Tôi rất yêu gia đình mình.')],50),
('weekend','Cuối tuần vui vẻ','giải trí',[
('星期六天气很好。','Thứ Bảy thời tiết rất đẹp.'),('我和朋友去公园。','Tôi và bạn đi công viên.'),('我们走路、看花，还喝茶。','Chúng tôi đi bộ, ngắm hoa và uống trà.'),('下午三点，我们回家。','Ba giờ chiều, chúng tôi về nhà.'),('今天大家都很高兴。','Hôm nay mọi người đều rất vui.')],50),
('shopping','Đi mua đồ','mua sắm',[
('妈妈要买水果。','Mẹ muốn mua trái cây.'),('我和妈妈一起去商店。','Tôi cùng mẹ đi cửa hàng.'),('苹果五块钱一斤，香蕉也不贵。','Táo năm tệ một cân, chuối cũng không đắt.'),('我们买了苹果、香蕉和牛奶。','Chúng tôi mua táo, chuối và sữa.'),('回家以后，我帮妈妈拿东西。','Sau khi về nhà, tôi giúp mẹ cầm đồ.')],50),
('newfriend','Người bạn mới','giao tiếp',[
('今天班里来了一位新同学。','Hôm nay lớp có một bạn học mới.'),('他叫王明，今年十岁。','Bạn ấy tên Vương Minh, năm nay mười tuổi.'),('他会说汉语和英语。','Bạn ấy biết nói tiếng Trung và tiếng Anh.'),('下课以后，我们一起看书。','Sau giờ học, chúng tôi cùng đọc sách.'),('现在我们是好朋友。','Bây giờ chúng tôi là bạn tốt.')],50),
],
2: [
('rainyday','Một ngày mưa','thời tiết',[
('今天早上突然下雨了，我出门的时候没有带伞。','Sáng nay trời đột nhiên mưa, lúc ra khỏi nhà tôi không mang ô.'),('走到车站以后，雨越来越大。','Sau khi đi đến trạm xe, mưa càng lúc càng lớn.'),('一位阿姨看见我，就让我和她一起打伞。','Một cô nhìn thấy tôi nên cho tôi đi chung ô.'),('到学校以后，我对她说了好几次谢谢。','Sau khi đến trường, tôi đã cảm ơn cô ấy nhiều lần.'),('这件小事让我觉得城市里有很多温暖的人。','Việc nhỏ này khiến tôi cảm thấy trong thành phố có rất nhiều người ấm áp.')],100),
('birthday','Sinh nhật của bà','gia đình',[
('星期天是奶奶的生日，全家人早早来到她家。','Chủ nhật là sinh nhật bà, cả nhà đến nhà bà từ sớm.'),('妈妈做了长寿面，爸爸买了一个大蛋糕。','Mẹ nấu mì trường thọ, bố mua một chiếc bánh lớn.'),('我和妹妹画了一张生日卡，还给奶奶唱了一首歌。','Tôi và em gái vẽ thiệp sinh nhật và hát tặng bà một bài.'),('奶奶笑着说，大家能回来吃饭就是最好的礼物。','Bà cười nói mọi người về ăn cơm đã là món quà tốt nhất.'),('那天我们拍了很多照片，每个人都很开心。','Hôm đó chúng tôi chụp nhiều ảnh, ai cũng vui.')],100),
('library','Buổi chiều ở thư viện','học tập',[
('下午没有课，我和小林去了学校图书馆。','Buổi chiều không có tiết, tôi và Tiểu Lâm đến thư viện trường.'),('那里很安静，桌子旁边还有很多绿色的植物。','Ở đó rất yên tĩnh, cạnh bàn còn có nhiều cây xanh.'),('我想找一本介绍中国城市的书，小林要准备明天的考试。','Tôi muốn tìm sách giới thiệu các thành phố Trung Quốc, còn Tiểu Lâm chuẩn bị cho kỳ thi ngày mai.'),('我们学习了两个小时，中间只休息了十分钟。','Chúng tôi học hai giờ, giữa giờ chỉ nghỉ mười phút.'),('离开以前，我们约好下周再来。','Trước khi rời đi, chúng tôi hẹn tuần sau lại đến.')],100),
('exercise','Tập thể dục cùng bố','sức khỏe',[
('爸爸每天工作很忙，但是他一直注意身体健康。','Bố mỗi ngày rất bận nhưng luôn chú ý sức khỏe.'),('晚上吃完饭以后，他常常带我到小区里跑步。','Sau bữa tối, bố thường dẫn tôi chạy bộ trong khu nhà.'),('开始的时候我跑得很慢，也觉得很累。','Lúc đầu tôi chạy rất chậm và cảm thấy mệt.'),('爸爸告诉我，不需要跑得快，只要每天坚持就会进步。','Bố nói không cần chạy nhanh, chỉ cần kiên trì mỗi ngày sẽ tiến bộ.'),('现在我已经能跟他一起跑三公里了。','Bây giờ tôi đã có thể chạy ba kilômét cùng bố.')],100),
('trip','Chuyến đi bằng tàu','du lịch',[
('去年暑假，我们一家坐火车去北方旅行。','Kỳ nghỉ hè năm ngoái, gia đình tôi đi tàu hỏa du lịch miền Bắc.'),('这是妹妹第一次坐火车，所以她看什么都觉得新鲜。','Đây là lần đầu em gái đi tàu nên nhìn gì cũng thấy mới lạ.'),('窗外有田地、河流和很远的山。','Ngoài cửa sổ có đồng ruộng, sông và núi xa.'),('我们在车上吃饭、聊天，还认识了一位热心的爷爷。','Chúng tôi ăn, trò chuyện trên tàu và làm quen một ông rất nhiệt tình.'),('虽然路上用了很长时间，但是大家一点儿也不觉得无聊。','Dù đi đường khá lâu nhưng mọi người không thấy chán chút nào.')],100),
],
3: [
('habit','Thói quen đọc sách','học tập',[
('以前我不太喜欢看书，放学以后总是先打开手机。','Trước đây tôi không thích đọc sách lắm, tan học luôn mở điện thoại trước.'),('后来老师建议我们每天安静地阅读二十分钟，并把有意思的内容写在笔记本上。','Sau đó giáo viên đề nghị mỗi ngày đọc yên tĩnh hai mươi phút và ghi nội dung thú vị vào sổ.'),('刚开始我觉得时间过得很慢，可是一个月以后，我发现自己能更快地理解文章，也学会了不少新词。','Ban đầu tôi thấy thời gian trôi rất chậm, nhưng sau một tháng tôi nhận ra mình hiểu bài nhanh hơn và học được nhiều từ mới.'),('现在，睡觉以前读几页书已经成了我的习惯。','Bây giờ đọc vài trang trước khi ngủ đã thành thói quen.'),('我也常常和同学交换书，听听他们对故事的看法。','Tôi cũng thường đổi sách với bạn và nghe quan điểm của họ về câu chuyện.'),('读书不但让我得到知识，还让我学会从不同的角度想问题。','Đọc sách không chỉ cho tôi kiến thức mà còn giúp tôi suy nghĩ từ nhiều góc độ.')],180),
('volunteer','Một ngày làm tình nguyện','xã hội',[
('上个星期六，学校组织我们去社区帮助老人。','Thứ Bảy tuần trước, trường tổ chức chúng tôi đến khu dân cư giúp người cao tuổi.'),('早上八点，我们带着水果和清洁工具来到活动中心。','Tám giờ sáng, chúng tôi mang trái cây và dụng cụ vệ sinh đến trung tâm hoạt động.'),('有的同学打扫房间，有的同学陪老人聊天，我负责教他们使用手机拍照。','Có bạn dọn phòng, có bạn trò chuyện với các cụ, tôi phụ trách dạy họ dùng điện thoại chụp ảnh.'),('一位爷爷开始很担心自己学不会，我就一步一步地给他说明。','Một ông ban đầu lo mình không học được, tôi giải thích từng bước.'),('当他第一次把照片发给家人时，脸上出现了开心的笑容。','Khi ông lần đầu gửi ảnh cho gia đình, gương mặt nở nụ cười vui.'),('这次活动让我明白，帮助别人不一定要做很大的事情，耐心和陪伴也非常重要。','Hoạt động này giúp tôi hiểu giúp người khác không nhất thiết phải làm việc lớn; kiên nhẫn và đồng hành cũng rất quan trọng.')],180),
('lostwallet','Chiếc ví bị mất','đời sống',[
('昨天中午，我在饭店吃完饭以后，发现钱包不见了。','Trưa hôm qua, sau khi ăn ở nhà hàng, tôi phát hiện mất ví.'),('钱包里有一些钱、银行卡，还有一张对我很重要的照片。','Trong ví có ít tiền, thẻ ngân hàng và một bức ảnh rất quan trọng với tôi.'),('我马上回到座位附近寻找，也问了服务员，但是谁都没有看见。','Tôi lập tức quay lại tìm gần chỗ ngồi và hỏi nhân viên nhưng không ai thấy.'),('正在我着急的时候，手机突然响了。','Khi tôi đang lo lắng, điện thoại đột nhiên reo.'),('原来一位客人在门口捡到了钱包，他从里面的名片上找到了我的号码。','Hóa ra một vị khách nhặt được ví ở cửa, tìm thấy số của tôi trên danh thiếp.'),('我赶过去向他道谢，他却说这只是每个人都应该做的事。','Tôi vội đến cảm ơn, nhưng ông nói đây chỉ là việc ai cũng nên làm.'),('从那以后，我每次离开座位前都会认真检查自己的东西。','Từ đó, mỗi lần rời chỗ tôi đều kiểm tra đồ cẩn thận.')],180),
('onlineclass','Học trực tuyến hiệu quả','học tập',[
('刚开始上网络课的时候，我以为在家学习会很轻松。','Khi mới học trực tuyến, tôi nghĩ học ở nhà sẽ rất thoải mái.'),('可是没有老师在旁边提醒，我常常一边听课一边看别的信息。','Nhưng không có giáo viên nhắc bên cạnh, tôi thường vừa nghe giảng vừa xem thông tin khác.'),('结果到了晚上，很多作业都没有完成。','Kết quả đến tối nhiều bài tập chưa xong.'),('后来我给自己做了一张时间表，上课时把手机放在另一个房间，休息十分钟以后再继续学习。','Sau đó tôi lập thời gian biểu, khi học để điện thoại ở phòng khác và nghỉ mười phút rồi học tiếp.'),('我还和同学建立了一个小组，每天互相报告学习进度。','Tôi còn lập nhóm với bạn, mỗi ngày báo cáo tiến độ cho nhau.'),('这些简单的方法让我变得更专心，也让我发现，自由并不等于没有计划。','Những cách đơn giản này giúp tôi tập trung hơn và nhận ra tự do không có nghĩa là không có kế hoạch.')],180),
('grandpa','Khu vườn của ông','thiên nhiên',[
('爷爷家后面有一个不大的菜园，里面种着西红柿、黄瓜和很多青菜。','Sau nhà ông có một vườn rau không lớn, trồng cà chua, dưa chuột và nhiều rau xanh.'),('小时候我只喜欢在旁边玩，不明白爷爷为什么每天都要去看一看。','Hồi nhỏ tôi chỉ thích chơi bên cạnh, không hiểu vì sao ông ngày nào cũng ra xem.'),('今年春天，爷爷让我自己种一棵小苗。','Mùa xuân năm nay, ông cho tôi tự trồng một cây con.'),('我给它浇水、除草，还记录它每天长高了多少。','Tôi tưới nước, nhổ cỏ và ghi lại mỗi ngày nó cao thêm bao nhiêu.'),('几个星期以后，小苗开出了黄色的花，后来结了三个红红的西红柿。','Vài tuần sau cây ra hoa vàng rồi kết ba quả cà chua đỏ.'),('吃到自己种的西红柿时，我第一次真正理解了爷爷的快乐。','Khi ăn cà chua do mình trồng, lần đầu tôi thực sự hiểu niềm vui của ông.'),('原来等待一件事慢慢成长，也是一种很特别的幸福。','Hóa ra chờ một điều dần trưởng thành cũng là một niềm hạnh phúc đặc biệt.')],180),
],
4: [
('choice','Một lựa chọn nghề nghiệp','công việc',[
('大学毕业前，我一直认为找到一份工资高的工作就是最重要的目标。','Trước khi tốt nghiệp đại học, tôi luôn cho rằng tìm được việc lương cao là mục tiêu quan trọng nhất.'),('因此，当两家公司同时给我机会时，我首先比较的是收入和办公室的位置。','Vì vậy, khi hai công ty cùng cho cơ hội, điều đầu tiên tôi so sánh là thu nhập và vị trí văn phòng.'),('第一家公司规模很大，工资也更高，可是工作内容比较单一，而且每天需要很长时间坐车。','Công ty thứ nhất quy mô lớn, lương cao hơn nhưng nội dung công việc khá đơn điệu và mỗi ngày phải đi xe rất lâu.'),('第二家公司虽然不大，却愿意让我参加不同的项目，负责人也认真地了解了我的兴趣和长期计划。','Công ty thứ hai tuy không lớn nhưng cho tôi tham gia nhiều dự án; người phụ trách cũng tìm hiểu nghiêm túc sở thích và kế hoạch dài hạn của tôi.'),('我和家人、老师谈了很多次，最后选择了第二家公司。','Tôi đã nói chuyện nhiều lần với gia đình và giáo viên, cuối cùng chọn công ty thứ hai.'),('刚开始，有些朋友觉得我放弃高工资很可惜。','Ban đầu, một số bạn thấy tiếc vì tôi bỏ lương cao.'),('但是半年以后，我已经学会独立完成项目，也越来越清楚自己想发展的方向。','Nhưng sau nửa năm, tôi đã học được cách tự hoàn thành dự án và càng rõ hướng mình muốn phát triển.'),('这段经历让我明白，选择工作不能只看眼前的条件，还要考虑学习机会、生活质量和个人价值。','Trải nghiệm này giúp tôi hiểu chọn việc không thể chỉ nhìn điều kiện trước mắt mà còn phải cân nhắc cơ hội học tập, chất lượng sống và giá trị cá nhân.')],300),
('citybike','Xe đạp công cộng trong thành phố','giao thông',[
('为了减少交通压力和空气污染，很多城市开始发展公共自行车。','Để giảm áp lực giao thông và ô nhiễm không khí, nhiều thành phố bắt đầu phát triển xe đạp công cộng.'),('使用者只要用手机找到附近的车辆，扫描二维码以后就可以骑走。','Người dùng chỉ cần dùng điện thoại tìm xe gần đó, quét mã là có thể đi.'),('这种方式价格不高，停车也方便，特别适合距离不太远的出行。','Cách này giá không cao, đỗ xe tiện, đặc biệt phù hợp quãng đường không xa.'),('不过，公共自行车带来方便的同时，也出现了一些问题。','Tuy nhiên, cùng với tiện lợi, xe đạp công cộng cũng gây ra một số vấn đề.'),('有人把车停在路中间，影响行人；有的车辆没有及时修理，使用起来不够安全。','Có người đỗ xe giữa đường ảnh hưởng người đi bộ; có xe không được sửa kịp thời nên không an toàn.'),('为了解决这些问题，管理部门设置了更多停车点，并要求公司定期检查车辆。','Để giải quyết, cơ quan quản lý đặt thêm điểm đỗ và yêu cầu công ty kiểm tra xe định kỳ.'),('市民也应该遵守规则，把车放在正确的位置，发现问题时及时报告。','Người dân cũng nên tuân thủ quy tắc, đặt xe đúng chỗ và báo kịp thời khi thấy vấn đề.'),('只有管理者、企业和使用者共同负责，这种绿色交通方式才能真正长期发展。','Chỉ khi cơ quan quản lý, doanh nghiệp và người dùng cùng chịu trách nhiệm, phương thức giao thông xanh này mới phát triển lâu dài.')],300),
('mistake','Giá trị của một sai lầm','học tập',[
('读高中的时候，我参加过一次重要的演讲比赛。','Khi học trung học, tôi từng tham gia một cuộc thi diễn thuyết quan trọng.'),('为了得到好成绩，我准备了很久，甚至把每一句话都背了下来。','Để đạt kết quả tốt, tôi chuẩn bị rất lâu, thậm chí học thuộc từng câu.'),('比赛开始以后，我因为太紧张，突然忘记了下一段内容。','Sau khi cuộc thi bắt đầu, vì quá căng thẳng tôi đột nhiên quên đoạn tiếp theo.'),('我站在台上沉默了十几秒，最后只好提前结束。','Tôi đứng im trên sân khấu hơn mười giây và đành kết thúc sớm.'),('当时我觉得非常丢脸，回家以后也不想和任何人说话。','Lúc đó tôi rất xấu hổ, về nhà không muốn nói với ai.'),('老师没有批评我，而是让我重新看比赛录像，找出真正的问题。','Giáo viên không phê bình mà bảo tôi xem lại video để tìm vấn đề thật sự.'),('我发现自己只注意记住文字，却没有真正理解内容，也没有练习在意外情况下继续表达。','Tôi nhận ra mình chỉ chú ý nhớ chữ mà chưa hiểu nội dung, cũng chưa luyện tiếp tục diễn đạt khi có tình huống bất ngờ.'),('后来我改变了准备方法，先整理观点，再用不同的话练习说明。','Sau đó tôi đổi cách chuẩn bị: sắp xếp quan điểm rồi luyện giải thích bằng cách nói khác nhau.'),('第二年我没有得到第一名，却完整、自信地讲完了自己的故事。','Năm sau tôi không đạt giải nhất nhưng đã kể trọn câu chuyện một cách tự tin.'),('那次失败让我懂得，错误并不可怕，重要的是能不能从中找到下一步的方向。','Thất bại đó giúp tôi hiểu sai lầm không đáng sợ; quan trọng là có tìm được hướng đi tiếp theo hay không.')],300),
('neighbors','Những người hàng xóm','cộng đồng',[
('我搬到现在的小区时，对周围的人和环境都不熟悉。','Khi chuyển đến khu nhà hiện tại, tôi không quen người và môi trường xung quanh.'),('每天上下班，我只是和邻居点点头，很少停下来交流。','Mỗi ngày đi làm, tôi chỉ gật đầu với hàng xóm, hiếm khi dừng lại trò chuyện.'),('有一天晚上，楼里的电梯突然坏了，一位住在六楼的老人提着很重的东西。','Một tối, thang máy trong tòa nhà hỏng, một cụ ở tầng sáu đang xách đồ nặng.'),('我帮她把东西送上楼，她请我进屋喝水，我们才第一次认真聊天。','Tôi giúp mang đồ lên, bà mời vào uống nước và lần đầu chúng tôi trò chuyện nghiêm túc.'),('后来我知道，她的孩子住在别的城市，平时只有她一个人在家。','Sau đó tôi biết con bà sống ở thành phố khác, thường bà ở nhà một mình.'),('从那以后，我去超市时会问她需不需要买什么，她也常常把自己做的点心送给我。','Từ đó, khi đi siêu thị tôi hỏi bà cần mua gì, bà cũng thường tặng tôi bánh tự làm.'),('慢慢地，更多邻居开始互相认识。','Dần dần, nhiều hàng xóm bắt đầu biết nhau.'),('有人建立了信息群，分享维修通知；有人周末带孩子一起活动。','Có người lập nhóm thông tin chia sẻ thông báo sửa chữa; có người cuối tuần cho trẻ hoạt động cùng nhau.'),('原来，一个社区是否温暖，不只取决于房子和设备，也取决于人们愿不愿意主动关心彼此。','Hóa ra một cộng đồng có ấm áp hay không không chỉ phụ thuộc nhà cửa và thiết bị mà còn ở việc mọi người có chủ động quan tâm nhau không.')],300),
('museum','Một chuyến tham quan bảo tàng','văn hóa',[
('上个月，老师带我们参观了城市历史博物馆。','Tháng trước, giáo viên dẫn chúng tôi tham quan bảo tàng lịch sử thành phố.'),('出发以前，我以为博物馆只是把旧东西放在玻璃柜里，可能会很无聊。','Trước khi đi, tôi nghĩ bảo tàng chỉ đặt đồ cũ trong tủ kính, có lẽ rất chán.'),('到了以后，讲解员先给每个人一张旧地图，让我们寻找现在学校所在的位置。','Khi đến, thuyết minh viên phát mỗi người một bản đồ cũ và cho tìm vị trí trường hiện nay.'),('我们发现，一百年前那里还是一片农田，附近只有一条很小的路。','Chúng tôi phát hiện một trăm năm trước nơi đó vẫn là ruộng, gần đó chỉ có con đường nhỏ.'),('展厅里还有过去的车票、商店广告和普通家庭使用的生活用品。','Phòng trưng bày còn có vé xe, quảng cáo cửa hàng và đồ sinh hoạt của gia đình xưa.'),('这些看起来平常的东西，让我第一次感觉历史并不是遥远的故事，而是很多普通人的日常生活。','Những vật bình thường này khiến tôi lần đầu cảm thấy lịch sử không phải chuyện xa xôi mà là đời sống thường ngày của nhiều người bình thường.'),('参观结束后，我们分组采访了家里的老人，记录他们年轻时城市的样子。','Sau tham quan, chúng tôi chia nhóm phỏng vấn người lớn tuổi trong nhà và ghi lại diện mạo thành phố khi họ trẻ.'),('通过这次活动，我不但了解了城市的变化，也更愿意听长辈讲过去的经历。','Qua hoạt động này, tôi không chỉ hiểu sự thay đổi của thành phố mà còn muốn nghe người lớn kể chuyện xưa hơn.')],300),
],
5: [
('remote','Làm việc từ xa và ranh giới cuộc sống','công việc',[
('近几年，远程工作从少数行业的特殊安排，逐渐变成许多公司可以选择的工作方式。','Những năm gần đây, làm việc từ xa từ một sắp xếp đặc biệt của ít ngành đã dần trở thành lựa chọn của nhiều công ty.'),('它最明显的优点是减少通勤时间，使员工能够更自由地安排工作地点。','Ưu điểm rõ nhất là giảm thời gian đi lại và giúp nhân viên tự do hơn trong việc sắp xếp nơi làm việc.'),('一些住得离公司很远的人因此可以多陪伴家人，也能把原来花在路上的时间用于运动或学习。','Một số người sống xa công ty nhờ đó có thêm thời gian bên gia đình và dùng thời gian đi đường trước đây để tập thể dục hoặc học tập.'),('然而，远程工作并不等于压力一定会减少。','Tuy nhiên, làm việc từ xa không có nghĩa áp lực chắc chắn giảm.'),('当办公室和家庭处在同一个空间里，工作时间很容易不断延长。','Khi văn phòng và gia đình ở cùng một không gian, giờ làm rất dễ kéo dài liên tục.'),('有的人早上醒来就开始回复信息，晚上休息时仍然担心错过同事的通知。','Có người vừa thức dậy đã trả lời tin nhắn, tối nghỉ vẫn lo bỏ lỡ thông báo của đồng nghiệp.'),('如果团队主要依靠文字交流，一些本来几分钟就能说明的问题，也可能因为理解不同而反复讨论。','Nếu nhóm chủ yếu giao tiếp bằng văn bản, vấn đề vốn giải thích vài phút có thể bị bàn đi bàn lại do hiểu khác nhau.'),('此外，新员工缺少面对面的观察和帮助，往往需要更长时间才能了解团队的习惯。','Ngoài ra, nhân viên mới thiếu quan sát và hỗ trợ trực tiếp nên thường cần lâu hơn để hiểu thói quen nhóm.'),('要让远程工作真正有效，公司和个人都需要建立清楚的规则。','Để làm việc từ xa thực sự hiệu quả, cả công ty và cá nhân cần xây dựng quy tắc rõ ràng.'),('公司应该明确任务目标、沟通渠道和回复时间，而不是把“随时在线”当作认真工作的证明。','Công ty nên xác định mục tiêu, kênh giao tiếp và thời gian phản hồi, thay vì coi “luôn trực tuyến” là bằng chứng làm việc nghiêm túc.'),('员工则可以设置固定的开始与结束时间，把工作设备放在相对独立的位置，并在休息时真正离开屏幕。','Nhân viên có thể đặt giờ bắt đầu và kết thúc cố định, để thiết bị làm việc ở vị trí tương đối riêng và thực sự rời màn hình khi nghỉ.'),('团队还应定期安排视频会议或线下活动，让成员有机会交流工作以外的想法。','Nhóm cũng nên định kỳ họp video hoặc hoạt động trực tiếp để thành viên trao đổi những ý tưởng ngoài công việc.'),('远程工作不是传统办公室的简单替代，而是一种需要重新设计管理方式和生活边界的制度。','Làm việc từ xa không phải sự thay thế đơn giản cho văn phòng truyền thống mà là chế độ cần thiết kế lại cách quản lý và ranh giới cuộc sống.'),('只有当效率、信任和休息得到平衡时，它的优势才能长期存在。','Chỉ khi hiệu suất, niềm tin và nghỉ ngơi được cân bằng, ưu thế của nó mới tồn tại lâu dài.')],600),
('learning','Học một kỹ năng trong thời đại thông tin','học tập',[
('互联网让学习资料变得前所未有地丰富。','Internet khiến tài liệu học tập phong phú hơn bao giờ hết.'),('无论想学外语、摄影、编程还是做饭，人们都能很快找到课程、文章和视频。','Dù muốn học ngoại ngữ, nhiếp ảnh, lập trình hay nấu ăn, mọi người đều nhanh chóng tìm được khóa học, bài viết và video.'),('但是，资料越来越多并不代表学习一定越来越容易。','Nhưng tài liệu càng nhiều không có nghĩa việc học chắc chắn dễ hơn.'),('许多人花了大量时间比较课程、收藏链接，却很少真正完成练习。','Nhiều người dành nhiều thời gian so sánh khóa học, lưu liên kết nhưng hiếm khi thật sự hoàn thành bài tập.'),('他们常常误以为“看懂了”就是“学会了”，直到需要独立完成任务时才发现知识并不牢固。','Họ thường tưởng “xem hiểu” là “đã học được”, đến khi cần tự làm mới phát hiện kiến thức chưa vững.'),('有效学习首先需要一个清楚而具体的目标。','Học hiệu quả trước hết cần một mục tiêu rõ và cụ thể.'),('“提高英语”太宽泛，而“一个月内听懂十段两分钟的日常对话”更容易执行和检查。','“Nâng cao tiếng Anh” quá rộng; còn “trong một tháng nghe hiểu mười đoạn hội thoại đời thường dài hai phút” dễ thực hiện và kiểm tra hơn.'),('其次，学习者应该尽快从输入转向输出。','Thứ hai, người học nên sớm chuyển từ tiếp nhận sang tạo ra.'),('看完一个解释以后，可以试着用自己的话总结；学了一个新词，就应在真实句子里使用；读完一章内容，则可以做一个小项目。','Sau khi xem giải thích, có thể thử tóm tắt bằng lời mình; học từ mới nên dùng trong câu thật; đọc xong một chương có thể làm dự án nhỏ.'),('错误在这个过程中并不是失败，而是帮助我们发现理解漏洞的信号。','Sai lầm trong quá trình này không phải thất bại mà là tín hiệu giúp phát hiện lỗ hổng hiểu biết.'),('再次，重复必须有间隔。','Thứ ba, lặp lại cần có khoảng cách.'),('同一天反复看十遍会产生熟悉感，却不一定形成长期记忆。','Xem đi xem lại mười lần trong một ngày tạo cảm giác quen nhưng chưa chắc tạo trí nhớ dài hạn.'),('在第二天、一周后和一个月后重新回忆，通常更能检验是否真正掌握。','Nhớ lại vào ngày hôm sau, một tuần và một tháng sau thường kiểm tra tốt hơn việc đã nắm thật sự hay chưa.'),('最后，学习计划必须允许调整。','Cuối cùng, kế hoạch học phải cho phép điều chỉnh.'),('如果某种方法长期没有效果，就应该根据记录改变材料、难度或练习方式，而不是只责怪自己不够努力。','Nếu một phương pháp lâu không hiệu quả, nên dựa vào ghi chép để thay tài liệu, độ khó hoặc cách luyện thay vì chỉ trách mình chưa đủ cố gắng.'),('在信息丰富的时代，真正稀缺的不是内容，而是选择、实践和持续反思的能力。','Trong thời đại thông tin phong phú, thứ thực sự khan hiếm không phải nội dung mà là khả năng lựa chọn, thực hành và liên tục suy ngẫm.')],600),
('tourism','Du lịch và đời sống địa phương','du lịch',[
('旅游业能够为一个地区带来收入、就业机会和更完善的公共设施。','Du lịch có thể mang lại thu nhập, việc làm và cơ sở công cộng tốt hơn cho một khu vực.'),('当越来越多游客到来时，餐馆、交通、住宿和文化服务都会得到发展。','Khi ngày càng nhiều du khách đến, nhà hàng, giao thông, lưu trú và dịch vụ văn hóa đều phát triển.'),('一些原来不被外界了解的传统手工艺，也可能通过旅游重新受到关注。','Một số nghề thủ công truyền thống trước đây ít được biết đến cũng có thể được chú ý trở lại nhờ du lịch.'),('然而，如果发展速度过快，旅游也会给当地生活带来压力。','Tuy nhiên, nếu phát triển quá nhanh, du lịch cũng gây áp lực cho đời sống địa phương.'),('热门地区的房租和物价可能上涨，居民熟悉的商店逐渐被纪念品店取代。','Tiền thuê và giá cả ở nơi nổi tiếng có thể tăng; cửa hàng quen thuộc dần bị thay bằng cửa hàng lưu niệm.'),('在节假日，大量车辆和游客还会造成拥堵、噪声和垃圾问题。','Vào ngày lễ, lượng lớn xe và khách còn gây tắc nghẽn, tiếng ồn và rác thải.'),('更重要的是，当文化活动完全按照游客的期待进行表演时，它可能失去原来的意义。','Quan trọng hơn, khi hoạt động văn hóa hoàn toàn biểu diễn theo kỳ vọng du khách, nó có thể mất ý nghĩa ban đầu.'),('可持续旅游因此强调一个原则：游客的体验不能以降低居民的生活质量为代价。','Du lịch bền vững vì thế nhấn mạnh nguyên tắc: trải nghiệm của du khách không được đánh đổi bằng chất lượng sống của cư dân.'),('地方政府可以限制某些区域每天的游客数量，改善公共交通，并把部分收入用于环境保护。','Chính quyền có thể giới hạn số khách mỗi ngày ở một số khu vực, cải thiện giao thông công cộng và dùng một phần thu nhập bảo vệ môi trường.'),('企业应该减少一次性用品，尊重劳动者权益，也应优先采购当地产品。','Doanh nghiệp nên giảm đồ dùng một lần, tôn trọng quyền người lao động và ưu tiên mua sản phẩm địa phương.'),('游客同样负有责任。','Du khách cũng có trách nhiệm.'),('出发前了解当地规则，进入宗教或历史场所时保持礼貌，不随意拍摄他人，都是基本的尊重。','Tìm hiểu quy định trước khi đi, giữ lịch sự ở nơi tôn giáo hoặc lịch sử, không tùy tiện chụp người khác đều là tôn trọng cơ bản.'),('与其只去拍一张相同的照片，不如多花时间听当地人介绍他们的生活。','Thay vì chỉ chụp một bức ảnh giống mọi người, nên dành thời gian nghe người địa phương giới thiệu cuộc sống.'),('一次负责任的旅行，不只是“看到了什么”，还包括我们以什么方式到达、消费和离开。','Một chuyến đi có trách nhiệm không chỉ là “đã thấy gì” mà còn gồm cách chúng ta đến, tiêu dùng và rời đi.'),('当旅游者与居民都能分享发展带来的好处时，旅行才会成为真正长久的交流。','Khi du khách và cư dân cùng chia sẻ lợi ích phát triển, du lịch mới trở thành sự giao lưu lâu dài thực sự.')],600),
('healthinfo','Đọc thông tin sức khỏe trên mạng','sức khỏe',[
('身体不舒服时，很多人的第一反应是拿出手机搜索症状。','Khi cơ thể khó chịu, phản ứng đầu tiên của nhiều người là lấy điện thoại tìm triệu chứng.'),('网络信息可以帮助我们了解常见问题，也能提醒人们及时就医。','Thông tin trên mạng có thể giúp hiểu vấn đề thường gặp và nhắc đi khám kịp thời.'),('但是，健康内容的质量差别很大。','Nhưng chất lượng nội dung sức khỏe rất khác nhau.'),('有些文章由专业机构发布，说明了资料来源和适用范围；有些内容却只用夸张的标题吸引注意。','Có bài do cơ quan chuyên môn đăng, nêu nguồn và phạm vi áp dụng; có nội dung chỉ dùng tiêu đề giật gân để thu hút.'),('如果读者只根据一两个相似的症状判断疾病，很容易过度担心，或者错过真正需要处理的问题。','Nếu chỉ dựa vào một hai triệu chứng giống nhau để đoán bệnh, người đọc dễ lo quá mức hoặc bỏ lỡ vấn đề thật sự cần xử lý.'),('判断健康信息是否可靠，可以先检查发布者是谁。','Để đánh giá thông tin sức khỏe đáng tin hay không, trước tiên có thể kiểm tra người công bố.'),('医院、大学、公共卫生机构和经过认证的专业组织通常比匿名账号更值得参考。','Bệnh viện, đại học, cơ quan y tế công cộng và tổ chức chuyên môn được chứng nhận thường đáng tham khảo hơn tài khoản ẩn danh.'),('其次，要看文章是否提供证据，是否说明研究对象、时间和限制。','Thứ hai, xem bài có cung cấp bằng chứng và nêu đối tượng nghiên cứu, thời gian, hạn chế hay không.'),('一项规模很小的研究，不能直接证明某种方法对所有人都有效。','Một nghiên cứu quy mô nhỏ không thể trực tiếp chứng minh một phương pháp hiệu quả với mọi người.'),('还要注意信息的日期，因为医学建议会随着新的证据而变化。','Cũng cần chú ý ngày thông tin vì khuyến nghị y khoa thay đổi theo bằng chứng mới.'),('最重要的是，网络资料不能代替医生对个人情况的检查。','Quan trọng nhất, tài liệu mạng không thể thay thế việc bác sĩ kiểm tra tình trạng cá nhân.'),('当症状严重、持续或突然出现时，应尽快寻求专业帮助，而不是不断更换关键词继续搜索。','Khi triệu chứng nghiêm trọng, kéo dài hoặc xuất hiện đột ngột, nên sớm tìm trợ giúp chuyên môn thay vì liên tục đổi từ khóa để tìm.'),('对于药物、治疗和饮食限制，也不应只听网友经验。','Với thuốc, điều trị và hạn chế ăn uống, cũng không nên chỉ nghe kinh nghiệm trên mạng.'),('正确使用网络健康信息的目的，不是自己完成诊断，而是更清楚地观察身体、准备问题，并与专业人员进行有效沟通。','Mục đích đúng của việc dùng thông tin sức khỏe trên mạng không phải tự chẩn đoán mà là quan sát cơ thể rõ hơn, chuẩn bị câu hỏi và giao tiếp hiệu quả với chuyên gia.')],600),
('repair','Văn hóa sửa chữa và tiêu dùng','môi trường',[
('现代商品更新很快，手机、家电和衣服还没有完全坏，人们就可能因为出现新款而想要更换。','Hàng hóa hiện đại đổi mới nhanh; điện thoại, đồ gia dụng và quần áo chưa hỏng hẳn, người ta đã muốn thay vì có mẫu mới.'),('这种消费方式给生活带来便利，也制造了大量资源浪费和垃圾。','Cách tiêu dùng này mang lại tiện lợi nhưng cũng tạo lãng phí tài nguyên và rác thải lớn.'),('一些产品设计得越来越难拆开，维修费用甚至接近购买新产品的价格。','Một số sản phẩm được thiết kế ngày càng khó tháo, chi phí sửa thậm chí gần giá mua mới.'),('于是，“坏了就换”逐渐成为常见选择。','Vì thế, “hỏng thì thay” dần thành lựa chọn phổ biến.'),('近年来，许多城市开始重新重视维修文化。','Những năm gần đây, nhiều thành phố bắt đầu coi trọng lại văn hóa sửa chữa.'),('社区里出现了维修活动，志愿者帮助居民检查小家电、缝补衣物或修理自行车。','Trong cộng đồng xuất hiện hoạt động sửa chữa; tình nguyện viên giúp cư dân kiểm tra đồ điện nhỏ, vá quần áo hoặc sửa xe đạp.'),('这些活动的意义不只是节省钱。','Ý nghĩa của những hoạt động này không chỉ là tiết kiệm tiền.'),('参与者能够了解物品的结构，学习基本工具的使用，也会更珍惜自己已经拥有的东西。','Người tham gia hiểu cấu tạo đồ vật, học dùng công cụ cơ bản và trân trọng hơn những gì đang có.'),('对老人来说，修好一台用了多年的收音机，可能还保留着重要的家庭记忆。','Với người cao tuổi, sửa được chiếc radio dùng nhiều năm có thể giữ lại ký ức gia đình quan trọng.'),('当然，维修并不适合所有情况。','Tất nhiên, sửa chữa không phù hợp mọi trường hợp.'),('涉及电池、高压电或重要安全功能的设备，需要由专业人员处理。','Thiết bị liên quan pin, điện áp cao hoặc chức năng an toàn quan trọng cần chuyên gia xử lý.'),('如果产品耗能很高，继续使用也可能比更换节能设备造成更大的环境负担。','Nếu sản phẩm tiêu thụ năng lượng cao, tiếp tục dùng có thể tạo gánh nặng môi trường lớn hơn thay bằng thiết bị tiết kiệm.'),('因此，合理的维修文化不是拒绝购买新东西，而是在更换以前认真判断：问题能否修复、修复是否安全、产品还能使用多久。','Vì vậy, văn hóa sửa chữa hợp lý không phải từ chối mua đồ mới mà là cân nhắc trước khi thay: có sửa được không, có an toàn không, còn dùng được bao lâu.'),('企业也应提供零件、说明和合理的维修服务，让消费者真正拥有选择。','Doanh nghiệp cũng nên cung cấp linh kiện, hướng dẫn và dịch vụ sửa hợp lý để người tiêu dùng thực sự có lựa chọn.'),('当设计者、生产者和使用者共同考虑产品的整个生命过程时，消费才可能变得更负责任。','Khi nhà thiết kế, nhà sản xuất và người dùng cùng cân nhắc toàn bộ vòng đời sản phẩm, tiêu dùng mới có thể có trách nhiệm hơn.')],600),
],
}


def build_reading() -> None:
    summaries = {}
    for level, items in PASSAGES.items():
        rows = [passage(level, *item) for item in items]
        payload = {
            'meta': {
                'level': str(level),
                'displayLevel': str(level),
                'version': '6.0.0',
                'targetCharacters': {1:50,2:100,3:180,4:300,5:600}[level],
                'passageCount': len(rows),
                'description': 'Bài đọc biên soạn theo độ dài mục tiêu, có pinyin và dịch từng câu.'
            },
            'passages': rows
        }
        (READING_DIR / f'hsk{level}.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        summaries[str(level)] = {'passages':len(rows),'lengths':[x['actualCharacters'] for x in rows]}
    (READING_DIR / 'meta.json').write_text(json.dumps({'version':'6.0.0','levels':summaries}, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    build_examples()
    build_reading()
    print('Built standardized examples and reading passages.')
