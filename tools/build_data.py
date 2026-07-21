#!/usr/bin/env python3
"""Build cleaned HSK 3.0 JSON from ivankra/hsk30 and Vietnamese CVDICT.

Expected inputs (not committed because of size/licensing):
  tools/source/hsk30.csv
  tools/source/CVDICT.u8
"""
from __future__ import annotations
import csv, json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'tools' / 'source'
OUT = ROOT / 'data' / 'levels'

POS_VI = {
    'N':'danh từ','V':'động từ','Adj':'tính từ','Adv':'phó từ','Pron':'đại từ',
    'Num':'số từ','M':'lượng từ','Prep':'giới từ','Conj':'liên từ','Aux':'trợ từ',
    'Int':'thán từ','Prefix':'tiền tố','Suffix':'hậu tố','Phonetic':'từ tượng thanh'
}

MANUAL_PRIMARY = {
    # Nghĩa HSK thông dụng đã được ưu tiên thủ công khi thứ tự từ điển quá rộng
    # hoặc đặt nghĩa ít dùng lên trước.
    'L1-0015':['gói; bọc', 'túi; bao', 'đảm nhận; bao gồm'],
    'L1-0017':['cốc; ly', 'lượng từ cho đồ uống đựng trong cốc hoặc ly', 'cúp; cúp vô địch'],
    'L1-0022':['lượng từ cho sách, vở', 'gốc; vốn; bản'],
    'L1-0023':['vở; sổ tay'],
    'L1-0025':['đừng; không được', 'khác; riêng biệt', 'rời khỏi; chia tay'],
    'L1-0035':['món ăn; thức ăn', 'rau'],
    'L1-0037':['kém; không tốt', 'sai; khác', 'thiếu'],
    'L1-0053':['lần; lượt', 'thứ tự; tiếp theo'],
    'L1-0076':['giờ; điểm', 'một chút', 'chấm; điểm số'],
    'L1-0077':['điện; điện năng'],
    'L1-0090':['đọc'],
    'L1-0103':['đặt; để', 'thả; buông', 'phát; chiếu'],
    'L1-0109':['phút', 'chia; phân', 'điểm'],
    'L1-0113':['làm; thực hiện', 'cán; thân; phần chính', 'quản lý'],
    'L1-0122':['với; cùng', 'theo; đi theo', 'gót chân'],
    'L1-0125':['đóng; tắt', 'cửa ải', 'liên quan'],
    'L1-0133':['hay là; hoặc là', 'vẫn; vẫn còn'],
    'L1-0143':['số; số hiệu', 'ngày trong tháng', 'cỡ; ký hiệu'],
    'L1-0151':['lời nói; câu nói', 'chuyện; lời'],
    'L1-0154':['trở về; quay lại', 'lần; lượt'],
    'L1-0172':['lượng từ cho phòng', 'giữa; khoảng'],
    'L1-0176':['gọi; kêu', 'tên là; được gọi là', 'bảo; yêu cầu'],
    'L1-0182':['vào; tiến vào'],
    'L1-0183':['đi vào đây; vào đây'],
    'L1-0190':['họp; tham dự cuộc họp'],
    'L1-0196':['thi; kiểm tra'],
    'L1-0197':['thi; kỳ thi; bài kiểm tra'],
    'L1-0207':['già; lớn tuổi', 'cũ; lâu năm', 'thường xuyên; luôn'],
    'L1-0213':['bên trong; trong', 'lớp lót'],
    'L1-0231':['lông; tóc', 'mao, một phần mười của tệ'],
    'L1-0235':['không sao; không có việc gì', 'rảnh; có thời gian'],
    'L1-0238':['cửa; cổng', 'lượng từ cho môn học'],
    'L1-0250':['nào; cái nào'],
    'L1-0259':['sữa', 'vú; ngực'],
    'L1-0289':['đứng dậy; ngồi dậy', 'bắt đầu; tiếp diễn'],
    'L1-0294':['tiền'],
    'L1-0304':['nóng; nóng bức', 'làm nóng'],
    'L1-0307':['nghiêm túc; chăm chỉ'],
    'L1-0308':['ngày', 'mặt trời'],
    'L1-0315':['trên; phía trên', 'lên', 'trước; vừa qua'],
    'L1-0333':['lúc; khi; thời điểm'],
    'L1-0352':['tặng; biếu', 'đưa; giao', 'tiễn'],
    'L1-0358':['quá; rất'],
    'L1-0365':['bạn học; bạn cùng lớp'],
    'L1-0372':['muộn; trễ', 'buổi tối'],
    'L1-0398':['ông; ngài; quý ông', 'chồng'],
    'L1-0400':['muốn; muốn làm', 'nghĩ; nhớ'],
    'L1-0403':['cô; tiểu thư', 'cô gái trẻ'],
    'L1-0416':['được; ổn; có thể', 'đi; di chuyển'],
    'L1-0422':['học viện; trường cao đẳng'],
    'L1-0433':['cùng nhau', 'một khối; một miếng', 'một đồng'],
    'L1-0437':['một chút; một ít', 'một điểm; một chấm'],
    'L1-0438':['cùng nhau; cùng một chỗ'],
    'L1-0452':['tháng', 'mặt trăng'],
    'L1-0455':['ở; tại', 'đang', 'tồn tại'],
    'L1-0461':['đứng', 'trạm; ga'],
    'L1-0472':['đang; đúng lúc', 'chính; đúng', 'thẳng'],
    'L1-0473':['đang'],
    'L1-0486':['chuẩn bị', 'sự chuẩn bị'],
    'L1-0490':['đi; đi bộ', 'rời đi'],
}

MANUAL_PINYIN_NUMBERED = {
    'L1-0044':'che1 shang5', 'L2-0034':'bu4 tai4', 'L2-0044':'bu4 yi1 hui4 r5',
    'L2-0264':'jian4 guo5', 'L2-0507':'song4 dao4', 'L2-0722':'zhe4 shi2 hou5',
    'L3-0192':'fang4 dao4', 'L3-0508':'neng2 bu4 neng2', 'L4-0853':'yan3 li5',
    'L4-0897':'you3 jin4 r5', 'L5-0108':'cheng2 li3', 'L6-0376':'hen3 nan2 shuo1',
    'L6-0957':'yi1 fan1', 'L6-1079':'zhi3 zhe5', 'L7-0253':'bu4 li4 yu2',
    'L7-0283':'bu4 ken3', 'L7-0286':'bu4 nan2', 'L7-0290':'bu4 ru2 shuo1',
    'L7-0300':'bu4 yu3', 'L7-0443':'chen4 zhe5', 'L7-0896':'ding4 wei2',
    'L7-1092':'fei1 wang3', 'L7-1362':'gong1 yi4 xing4', 'L7-1743':'huai2 zhe5',
    'L7-2561':'li2 pu3 r5', 'L7-2972':'nan2 yi3 xiang3 xiang4',
    'L7-3893':'shuo1 qi3 lai5', 'L7-4577':'xiao4 fang3',
    'L7-5399':'zhi4 li4 yu2', 'L7-5538':'zhuo2 yan3 yu2'
}

MANUAL_MISSING = {
    'L1-0044':['trên xe'], 'L2-0034':['không lắm; không quá'],
    'L2-0044':['chẳng bao lâu; một lát sau'], 'L2-0264':['đã từng gặp; từng thấy'],
    'L2-0507':['đưa/gửi đến'], 'L2-0722':['lúc này; khi đó'],
    'L3-0192':['đặt vào; để đến'], 'L3-0508':['có thể hay không; có… được không'],
    'L4-0853':['trong mắt; theo cách nhìn'], 'L4-0897':['có sức; có hứng'],
    'L5-0108':['trong thành phố'], 'L6-0376':['khó nói; chưa thể kết luận'],
    'L6-0957':['một phen; một lượt'], 'L6-1079':['chỉ vào; trỏ vào'],
    'L7-0253':['không có lợi cho'], 'L7-0283':['không chịu; không đồng ý'],
    'L7-0286':['không khó'], 'L7-0290':['nói đúng hơn là'], 'L7-0300':['không cấp; không cho phép'],
    'L7-0443':['nhân lúc; tranh thủ khi'], 'L7-0891':['đủ dùng; đủ khả năng'],
    'L7-1680':['không hề; hoàn toàn không'], 'L7-2169':['xem như; coi như'],
    'L7-2863':['rất khó; khó mà'], 'L7-3314':['nói chung là'],
    'L7-3972':['theo đó; nhờ vậy'], 'L7-5025':['không đến mức; chưa tới mức'],
    'L7-5276':['có thể thấy rằng'],
    'L7-0896':['định là; quy định là'],
    'L7-1092':['bay đến; bay tới'],
    'L7-1127':['dặn dò; sai bảo'],
    'L7-1362':['tính công ích; tính phục vụ lợi ích công cộng'],
    'L7-1743':['mang trong lòng; ôm ấp một tâm trạng'],
    'L7-2561':['vô lý; quá đáng; lệch xa thực tế'],
    'L7-2972':['khó tưởng tượng'],
    'L7-3893':['nói đến; xét ra'],
    'L7-4577':['noi theo; bắt chước'],
    'L7-5100':['đồng thời; cùng lúc đó'],
    'L7-5399':['dốc sức vào; tận tâm với'],
    'L7-5463':['căn dặn; dặn dò'],
    'L7-5538':['chú trọng vào; hướng tới']
}

# Starter examples reviewed for simple grammar and natural meaning.
EXAMPLES = {
'爱':('我爱我的家人。','Wǒ ài wǒ de jiārén.','Tôi yêu gia đình của mình.'),
'爱好':('我的爱好是学中文。','Wǒ de àihào shì xué Zhōngwén.','Sở thích của tôi là học tiếng Trung.'),
'爸爸':('我爸爸今天上班。','Wǒ bàba jīntiān shàngbān.','Hôm nay bố tôi đi làm.'),
'妈妈':('妈妈在家做饭。','Māma zài jiā zuòfàn.','Mẹ đang nấu cơm ở nhà.'),
'家':('我家有四个人。','Wǒ jiā yǒu sì ge rén.','Nhà tôi có bốn người.'),
'人':('这里有很多人。','Zhèlǐ yǒu hěn duō rén.','Ở đây có rất nhiều người.'),
'中国':('我想去中国旅行。','Wǒ xiǎng qù Zhōngguó lǚxíng.','Tôi muốn đi du lịch Trung Quốc.'),
'中文':('我每天学习中文。','Wǒ měitiān xuéxí Zhōngwén.','Tôi học tiếng Trung mỗi ngày.'),
'老师':('老师说得很清楚。','Lǎoshī shuō de hěn qīngchu.','Giáo viên nói rất rõ.'),
'学生':('他是大学生。','Tā shì dàxuéshēng.','Anh ấy là sinh viên đại học.'),
'同学':('她是我的同学。','Tā shì wǒ de tóngxué.','Cô ấy là bạn học của tôi.'),
'朋友':('我们是好朋友。','Wǒmen shì hǎo péngyou.','Chúng tôi là bạn tốt.'),
'名字':('你的名字是什么？','Nǐ de míngzi shì shénme?','Tên của bạn là gì?'),
'你好':('你好，很高兴认识你。','Nǐ hǎo, hěn gāoxìng rènshi nǐ.','Xin chào, rất vui được biết bạn.'),
'谢谢':('谢谢你的帮助。','Xièxie nǐ de bāngzhù.','Cảm ơn sự giúp đỡ của bạn.'),
'再见':('明天见，再见！','Míngtiān jiàn, zàijiàn!','Hẹn gặp ngày mai, tạm biệt!'),
'对不起':('对不起，我来晚了。','Duìbuqǐ, wǒ lái wǎn le.','Xin lỗi, tôi đến muộn.'),
'没关系':('没关系，下次注意。','Méi guānxi, xià cì zhùyì.','Không sao, lần sau chú ý nhé.'),
'请':('请坐，请喝茶。','Qǐng zuò, qǐng hē chá.','Mời ngồi, mời uống trà.'),
'请问':('请问，地铁站在哪儿？','Qǐngwèn, dìtiězhàn zài nǎr?','Xin hỏi, ga tàu điện ngầm ở đâu?'),
'今天':('今天天气很好。','Jīntiān tiānqì hěn hǎo.','Hôm nay thời tiết rất đẹp.'),
'明天':('明天我们去公园。','Míngtiān wǒmen qù gōngyuán.','Ngày mai chúng ta đi công viên.'),
'昨天':('昨天我没有上班。','Zuótiān wǒ méiyǒu shàngbān.','Hôm qua tôi không đi làm.'),
'现在':('我现在有时间。','Wǒ xiànzài yǒu shíjiān.','Bây giờ tôi có thời gian.'),
'上午':('我上午八点上班。','Wǒ shàngwǔ bā diǎn shàngbān.','Tôi đi làm lúc tám giờ sáng.'),
'中午':('我们中午一起吃饭。','Wǒmen zhōngwǔ yìqǐ chīfàn.','Buổi trưa chúng ta cùng ăn cơm.'),
'下午':('下午我要开会。','Xiàwǔ wǒ yào kāihuì.','Buổi chiều tôi phải họp.'),
'晚上':('我晚上十点睡觉。','Wǒ wǎnshang shí diǎn shuìjiào.','Tôi ngủ lúc mười giờ tối.'),
'吃':('我想吃米饭。','Wǒ xiǎng chī mǐfàn.','Tôi muốn ăn cơm.'),
'喝':('你想喝茶还是咖啡？','Nǐ xiǎng hē chá háishi kāfēi?','Bạn muốn uống trà hay cà phê?'),
'水':('请给我一杯水。','Qǐng gěi wǒ yì bēi shuǐ.','Cho tôi một cốc nước.'),
'茶':('爸爸喜欢喝茶。','Bàba xǐhuan hē chá.','Bố thích uống trà.'),
'米饭':('我每天都吃米饭。','Wǒ měitiān dōu chī mǐfàn.','Tôi ăn cơm mỗi ngày.'),
'菜':('这个菜很好吃。','Zhège cài hěn hǎochī.','Món này rất ngon.'),
'水果':('多吃水果对身体好。','Duō chī shuǐguǒ duì shēntǐ hǎo.','Ăn nhiều trái cây tốt cho sức khỏe.'),
'苹果':('我买了三个苹果。','Wǒ mǎi le sān ge píngguǒ.','Tôi đã mua ba quả táo.'),
'买':('我要去超市买东西。','Wǒ yào qù chāoshì mǎi dōngxi.','Tôi sẽ đi siêu thị mua đồ.'),
'钱':('我今天没带钱。','Wǒ jīntiān méi dài qián.','Hôm nay tôi không mang tiền.'),
'工作':('我的工作很忙。','Wǒ de gōngzuò hěn máng.','Công việc của tôi rất bận.'),
'上班':('他每天八点上班。','Tā měitiān bā diǎn shàngbān.','Anh ấy đi làm lúc tám giờ mỗi ngày.'),
'下班':('我五点半下班。','Wǒ wǔ diǎn bàn xiàbān.','Tôi tan làm lúc năm giờ rưỡi.'),
'学习':('孩子们正在学习。','Háizimen zhèngzài xuéxí.','Các em nhỏ đang học.'),
'考试':('明天我们有考试。','Míngtiān wǒmen yǒu kǎoshì.','Ngày mai chúng tôi có kỳ thi.'),
'看':('我喜欢看电影。','Wǒ xǐhuan kàn diànyǐng.','Tôi thích xem phim.'),
'听':('我每天听中文。','Wǒ měitiān tīng Zhōngwén.','Tôi nghe tiếng Trung mỗi ngày.'),
'说':('请慢一点儿说。','Qǐng màn yìdiǎnr shuō.','Xin hãy nói chậm một chút.'),
'读':('他在房间里读书。','Tā zài fángjiān li dúshū.','Anh ấy đang đọc sách trong phòng.'),
'写':('请写下你的名字。','Qǐng xiě xià nǐ de míngzi.','Hãy viết tên của bạn xuống.'),
'去':('周末我去公园。','Zhōumò wǒ qù gōngyuán.','Cuối tuần tôi đi công viên.'),
'来':('欢迎你来我家。','Huānyíng nǐ lái wǒ jiā.','Hoan nghênh bạn đến nhà tôi.'),
'走':('我们一起走吧。','Wǒmen yìqǐ zǒu ba.','Chúng ta cùng đi nhé.'),
'坐':('我坐公共汽车上班。','Wǒ zuò gōnggòng qìchē shàngbān.','Tôi đi làm bằng xe buýt.'),
'开车':('他每天开车上班。','Tā měitiān kāichē shàngbān.','Anh ấy lái xe đi làm mỗi ngày.'),
'回家':('下班以后我回家。','Xiàbān yǐhòu wǒ huí jiā.','Sau khi tan làm tôi về nhà.'),
'医院':('他去医院看医生。','Tā qù yīyuàn kàn yīshēng.','Anh ấy đến bệnh viện khám bác sĩ.'),
'医生':('医生让我多休息。','Yīshēng ràng wǒ duō xiūxi.','Bác sĩ bảo tôi nghỉ ngơi nhiều.'),
'身体':('运动对身体很好。','Yùndòng duì shēntǐ hěn hǎo.','Vận động rất tốt cho cơ thể.'),
'休息':('累了就休息一下。','Lèi le jiù xiūxi yíxià.','Mệt thì nghỉ một chút.'),
'运动':('我每天早上运动。','Wǒ měitiān zǎoshang yùndòng.','Tôi tập thể dục mỗi sáng.'),
'天气':('今天天气有点儿冷。','Jīntiān tiānqì yǒudiǎnr lěng.','Hôm nay thời tiết hơi lạnh.'),
'下雨':('外面正在下雨。','Wàimian zhèngzài xiàyǔ.','Bên ngoài đang mưa.'),
'热':('今天太热了。','Jīntiān tài rè le.','Hôm nay nóng quá.'),
'冷':('冬天这里很冷。','Dōngtiān zhèlǐ hěn lěng.','Mùa đông ở đây rất lạnh.'),
'高兴':('见到你我很高兴。','Jiàndào nǐ wǒ hěn gāoxìng.','Gặp bạn tôi rất vui.'),
'喜欢':('我喜欢学汉语。','Wǒ xǐhuan xué Hànyǔ.','Tôi thích học tiếng Trung.'),
'想':('我想喝一杯咖啡。','Wǒ xiǎng hē yì bēi kāfēi.','Tôi muốn uống một cốc cà phê.'),
'知道':('我不知道他的名字。','Wǒ bù zhīdào tā de míngzi.','Tôi không biết tên anh ấy.'),
'认识':('你认识那个人吗？','Nǐ rènshi nàge rén ma?','Bạn có biết người kia không?'),
'帮助':('谢谢你帮助我。','Xièxie nǐ bāngzhù wǒ.','Cảm ơn bạn đã giúp tôi.'),
'问题':('我有一个问题。','Wǒ yǒu yí ge wèntí.','Tôi có một câu hỏi.'),
'时间':('你什么时候有时间？','Nǐ shénme shíhou yǒu shíjiān?','Khi nào bạn có thời gian?'),
'因为':('因为下雨，所以我没出去。','Yīnwèi xiàyǔ, suǒyǐ wǒ méi chūqu.','Vì trời mưa nên tôi không ra ngoài.'),
'所以':('我很累，所以想休息。','Wǒ hěn lèi, suǒyǐ xiǎng xiūxi.','Tôi rất mệt nên muốn nghỉ.'),
'但是':('这件衣服很好看，但是太贵了。','Zhè jiàn yīfu hěn hǎokàn, dànshì tài guì le.','Bộ quần áo này đẹp nhưng quá đắt.'),
'如果':('如果有时间，我就去。','Rúguǒ yǒu shíjiān, wǒ jiù qù.','Nếu có thời gian, tôi sẽ đi.'),
'一起':('我们一起学习吧。','Wǒmen yìqǐ xuéxí ba.','Chúng ta cùng học nhé.'),
'已经':('我已经吃过饭了。','Wǒ yǐjīng chīguo fàn le.','Tôi đã ăn cơm rồi.'),
'正在':('他正在打电话。','Tā zhèngzài dǎ diànhuà.','Anh ấy đang gọi điện thoại.'),
'可能':('他今天可能不来。','Tā jīntiān kěnéng bù lái.','Hôm nay có thể anh ấy không đến.'),
'重要':('健康比什么都重要。','Jiànkāng bǐ shénme dōu zhòngyào.','Sức khỏe quan trọng hơn tất cả.'),
'简单':('这个问题很简单。','Zhège wèntí hěn jiǎndān.','Câu hỏi này rất đơn giản.'),
'困难':('遇到困难不要放弃。','Yùdào kùnnan bú yào fàngqì.','Gặp khó khăn đừng bỏ cuộc.'),
'成功':('努力是成功的重要条件。','Nǔlì shì chénggōng de zhòngyào tiáojiàn.','Nỗ lực là điều kiện quan trọng để thành công.'),
'和平':('大家都希望世界和平。','Dàjiā dōu xīwàng shìjiè hépíng.','Mọi người đều mong thế giới hòa bình.')
}

LINE_RE = re.compile(r'^(\S+) (\S+) \[([^\]]+)\] /(.*)/$')
KEY_RE = re.compile(r'([^|]+)\|([^\[]+)\[([^\]]+)\]')

def clean_def(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:260]

def is_reference_meaning(text: str) -> bool:
    low = text.lower().strip()
    if low.startswith(('biến thể của ', 'biến thể cũ của ', 'biến thể er hoá của ',
                       'cách viết thay thế của ', 'dạng viết khác của ', 'viết tắt của ')):
        return True
    return bool(re.match(r'^xem\s+[\u3400-\u9fff]', low))

def ordered_meanings(records):
    meaningful=[]; references=[]
    # CEDICT dùng pinyin viết hoa cho tên riêng. Nếu cùng chữ/cùng âm có cả bản
    # viết thường và viết hoa, chỉ giữ bản viết thường để tránh trộn họ/địa danh
    # vào nghĩa HSK thông dụng. Nếu chỉ có tên riêng thì vẫn giữ nguyên.
    common_records=[r for r in records if r.get('pinyinNumbered','')[:1].islower()]
    if common_records:
        records=common_records
    records=sorted(
        records,
        key=lambda r: -sum(not is_reference_meaning(x) for x in r['meanings'])
    )
    for rec in records:
        for meaning in rec['meanings']:
            target = references if is_reference_meaning(meaning) else meaningful
            if meaning not in meaningful and meaning not in references:
                target.append(meaning)
    return meaningful or references

def resolve_reference_meanings(meanings, by_simp):
    # Thay chỉ dẫn “biến thể/xem…” bằng nghĩa của mục từ gốc nếu tìm được.
    if not meanings or any(not is_reference_meaning(x) for x in meanings):
        return meanings
    for meaning in meanings:
        match=re.search(r'(?:của|xem)\s+([\u3400-\u9fff]+)(?:\|([\u3400-\u9fff]+))?', meaning, flags=re.I)
        if not match:
            continue
        base_records=by_simp.get(match.group(2) or match.group(1), [])
        base_meanings=ordered_meanings(base_records)
        common=[x for x in base_meanings if not is_reference_meaning(x)]
        if common:
            return common + meanings
    return meanings

def load_cvdict(path: Path):
    by_triple = defaultdict(list)
    by_key = defaultdict(list)
    by_simp = defaultdict(list)
    with path.open(encoding='utf-8') as f:
        for line in f:
            line=line.rstrip('\n')
            if not line or line.startswith('#'): continue
            m=LINE_RE.match(line)
            if not m: continue
            trad,simp,pinyin,defs=m.groups()
            meanings=[clean_def(x) for x in defs.split('/') if x.strip()]
            rec={'traditional':trad,'simplified':simp,'pinyinNumbered':pinyin,'meanings':meanings}
            by_triple[(trad,simp,pinyin.lower())].append(rec)
            by_key[(simp,pinyin.lower())].append(rec)
            by_simp[simp].append(rec)
    return by_triple, by_key, by_simp

def variants_from(row):
    if row['Variants']:
        try:
            raw=json.loads(row['Variants'])
            return [
                {'simplified':x.get('Simplified',''), 'traditional':x.get('Traditional',''),
                 'pinyin':x.get('Pinyin',''), 'isExample':bool(x.get('Example'))}
                for x in raw
            ]
        except Exception:
            pass
    return []

def build(hsk_path: Path, cv_path: Path):
    by_triple, by_key, by_simp = load_cvdict(cv_path)
    levels=defaultdict(list)
    status_count=defaultdict(int)
    with hsk_path.open(encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            recs=[]
            numbered_pinyin=''
            for part in row['CEDICT'].split('/'):
                m=KEY_RE.match(part)
                if m:
                    numbered_pinyin = numbered_pinyin or m.group(3)
                    # Ưu tiên đúng cả phồn thể + giản thể + pinyin để tránh trộn các từ
                    # đồng hình như 後/后, 裡/里, 乾/干.
                    matches=by_triple.get((m.group(1),m.group(2),m.group(3).lower()), [])
                    if not matches:
                        matches=by_key.get((m.group(2),m.group(3).lower()), [])
                    for rec in matches:
                        if rec not in recs: recs.append(rec)
            if row['ID'] in MANUAL_PRIMARY:
                meanings=MANUAL_PRIMARY[row['ID']]
                status='kiem_tra_thu_cong'
            elif recs:
                meanings=resolve_reference_meanings(ordered_meanings(recs), by_simp)
                status='doi_chieu_chinh_xac'
            elif row['ID'] in MANUAL_MISSING:
                meanings=MANUAL_MISSING[row['ID']]
                status='kiem_tra_thu_cong'
            else:
                simp=row['Simplified'].split('|')[0]
                candidates=by_simp.get(simp,[])
                meanings=resolve_reference_meanings(ordered_meanings(candidates), by_simp) if candidates else ['Cần rà soát nghĩa tiếng Việt']
                status='can_ra_soat'
            meanings=[m for m in meanings if m][:8] or ['Cần rà soát nghĩa tiếng Việt']
            senses=[{'id':f"{row['ID'].lower()}-s{i+1:02d}",'vi':meaning} for i,meaning in enumerate(meanings)]
            simp=row['Simplified'].split('|')[0]
            example=EXAMPLES.get(simp)
            word={
                'id':row['ID'], 'level':'7' if row['Level']=='7-9' else row['Level'],
                'simplified':simp, 'traditional':row['Traditional'].split('|')[0],
                'pinyin':row['Pinyin'].split('|')[0],
                'pinyinNumbered':numbered_pinyin or MANUAL_PINYIN_NUMBERED.get(row['ID'], ''), 'pos':[POS_VI.get(p,p) for p in row['POS'].split('/') if p],
                'senses':senses, 'meaning':senses[0]['vi'], 'variants':variants_from(row),
                'verification':status,
                'example':({'zh':example[0],'pinyin':example[1],'vi':example[2],'status':'da_duyet'} if example else None)
            }
            levels[word['level']].append(word)
            status_count[status]+=1
    OUT.mkdir(parents=True,exist_ok=True)
    meta={'schemaVersion':1,'totalWords':sum(map(len,levels.values())),
          'levels':{k:len(v) for k,v in levels.items()},'verification':dict(status_count),
          'exampleCount':sum(1 for vs in levels.values() for w in vs if w['example']),
          'sources':['ivankra/hsk30','ph0ngp/CVDICT'],'generatedBy':'tools/build_data.py'}
    for level in sorted(levels,key=lambda x:int(x)):
        (OUT/f'hsk{level}.json').write_text(json.dumps({'meta':{'level':level,'count':len(levels[level])},'words':levels[level]},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (ROOT/'data'/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__=='__main__':
    hsk=Path(sys.argv[1]) if len(sys.argv)>1 else SRC/'hsk30.csv'
    cv=Path(sys.argv[2]) if len(sys.argv)>2 else SRC/'CVDICT.u8'
    build(hsk,cv)
