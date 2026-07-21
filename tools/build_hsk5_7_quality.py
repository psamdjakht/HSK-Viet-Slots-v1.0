#!/usr/bin/env python3
"""Build additive quality packs for HSK 5, HSK 6 and the app's HSK 7–9 bundle.
This script never writes HSK 1–4 files.
"""
from __future__ import annotations
import importlib.util, json, re, bisect
from collections import defaultdict
from pathlib import Path
from pypinyin import lazy_pinyin, Style

ROOT = Path(__file__).resolve().parents[1]
BASE_SCRIPT = ROOT / 'tools/build_hsk2_4_quality.py'
spec = importlib.util.spec_from_file_location('base_quality', BASE_SCRIPT)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
LEVELS = (5, 6, 7)
TODAY = '2026-07-21'

PRIMARY_OVERRIDES = {
  '安慰':'an ủi; động viên','避免':'tránh; phòng tránh','承担':'đảm nhận; gánh chịu','促进':'thúc đẩy',
  '独立':'độc lập','发挥':'phát huy','反映':'phản ánh','改善':'cải thiện','沟通':'giao tiếp; trao đổi',
  '构成':'cấu thành','观察':'quan sát','规模':'quy mô','价值':'giá trị','具备':'có đủ; hội đủ',
  '培养':'bồi dưỡng; đào tạo','评价':'đánh giá','趋势':'xu hướng','确认':'xác nhận','申请':'đăng ký; xin',
  '实现':'thực hiện; hiện thực hóa','适应':'thích nghi','维护':'duy trì; bảo vệ','限制':'hạn chế',
  '形成':'hình thành','预防':'phòng ngừa','赞成':'tán thành','造成':'gây ra','执行':'thi hành; thực hiện',
  '挨着':'sát cạnh; ở gần','颁布':'ban hành','包袱':'gánh nặng; bọc hành lý','保管':'bảo quản; trông giữ',
  '报酬':'thù lao','抱怨':'phàn nàn','本领':'bản lĩnh; năng lực','比例':'tỷ lệ','辩护':'biện hộ',
  '补偿':'bồi thường; bù đắp','策划':'lập kế hoạch; hoạch định','差距':'khoảng cách; chênh lệch',
  '撤销':'hủy bỏ; thu hồi','沉淀':'lắng đọng; kết tủa','诚恳':'chân thành','冲突':'xung đột',
  '储备':'dự trữ','处分':'xử lý kỷ luật','传达':'truyền đạt','创立':'thành lập','担保':'bảo lãnh',
  '抵制':'chống lại; tẩy chay','动机':'động cơ','断定':'khẳng định; kết luận chắc chắn','对策':'đối sách',
  '方针':'phương châm; đường lối','分寸':'mức độ chừng mực','风险':'rủi ro','否决':'bác bỏ; phủ quyết',
  '敷衍':'qua loa; đối phó','干涉':'can thiệp','根源':'căn nguyên','贯彻':'quán triệt; thực hiện xuyên suốt',
  '归纳':'quy nạp; tổng hợp','过渡':'quá độ; chuyển tiếp','核心':'cốt lõi','缓和':'làm dịu; hòa hoãn',
  '监督':'giám sát','局势':'tình thế; cục diện','可靠':'đáng tin cậy','扩散':'khuếch tán; lan rộng',
  '理念':'quan niệm; triết lý','弥补':'bù đắp','逆转':'đảo ngược','排斥':'bài xích; loại trừ',
  '偏见':'định kiến','评估':'đánh giá; thẩm định','迫切':'cấp thiết','潜力':'tiềm lực; tiềm năng',
  '权衡':'cân nhắc; cân đối','实施':'thực thi','适宜':'thích hợp','体谅':'thông cảm; thấu hiểu',
  '推测':'suy đoán','协调':'phối hợp; điều hòa','需求':'nhu cầu','预期':'dự kiến; kỳ vọng','约束':'ràng buộc',
  '指标':'chỉ tiêu; chỉ số','倡导':'đề xướng; vận động','遏制':'kiềm chế; ngăn chặn','秉持':'giữ vững; tuân giữ',
  '筹措':'thu xếp; huy động','斟酌':'cân nhắc kỹ','凸显':'làm nổi bật','诠释':'giải thích; diễn giải',
  '契机':'cơ hội; thời cơ','取缔':'cấm; đình chỉ','搁置':'gác lại','梳理':'sắp xếp, hệ thống hóa',
  '诉求':'yêu cầu; nguyện vọng','推崇':'tôn sùng; đề cao','统筹':'điều phối tổng thể','妥善':'thỏa đáng; ổn thỏa',
  '衔接':'kết nối; tiếp nối','研判':'nghiên cứu và phán đoán','制约':'hạn chế; chế ước','着力':'tập trung sức lực',
}

CURATED_COLLOCATIONS = {
 '安慰':['安慰朋友','得到安慰','安慰自己'],'承担':['承担责任','承担风险','承担费用'],
 '促进':['促进发展','促进交流','促进合作'],'发挥':['发挥作用','发挥优势','充分发挥'],
 '改善':['改善生活','改善环境','明显改善'],'沟通':['加强沟通','沟通问题','有效沟通'],
 '构成':['构成威胁','构成部分','基本构成'],'观察':['仔细观察','观察情况','长期观察'],
 '规模':['扩大规模','经营规模','达到规模'],'价值':['实际价值','创造价值','具有价值'],
 '培养':['培养能力','培养习惯','培养人才'],'评价':['作出评价','客观评价','评价标准'],
 '趋势':['发展趋势','总体趋势','呈现趋势'],'确认':['确认信息','得到确认','再次确认'],
 '申请':['提出申请','申请工作','申请材料'],'实现':['实现目标','实现梦想','逐步实现'],
 '适应':['适应环境','适应变化','逐渐适应'],'维护':['维护权益','维护秩序','维护关系'],
 '限制':['受到限制','限制条件','严格限制'],'预防':['预防疾病','提前预防','预防措施'],
 '执行':['执行任务','严格执行','执行计划'],'报酬':['劳动报酬','获得报酬','支付报酬'],
 '差距':['缩小差距','存在差距','明显差距'],'冲突':['发生冲突','利益冲突','避免冲突'],
 '储备':['人才储备','物资储备','储备力量'],'传达':['传达精神','传达信息','准确传达'],
 '动机':['学习动机','行为动机','动机明确'],'对策':['采取对策','应对对策','提出对策'],
 '风险':['降低风险','承担风险','风险评估'],'贯彻':['贯彻落实','贯彻精神','全面贯彻'],
 '核心':['核心问题','核心价值','核心技术'],'监督':['接受监督','加强监督','监督管理'],
 '理念':['发展理念','教育理念','经营理念'],'评估':['风险评估','进行评估','综合评估'],
 '潜力':['发展潜力','发挥潜力','市场潜力'],'协调':['协调关系','协调发展','相互协调'],
 '需求':['市场需求','满足需求','实际需求'],'约束':['制度约束','受到约束','约束条件'],
 '倡导':['倡导文明','积极倡导','倡导节约'],'遏制':['遏制增长','有效遏制','遏制风险'],
 '筹措':['筹措资金','多方筹措','筹措经费'],'梳理':['梳理问题','系统梳理','梳理流程'],
 '诉求':['合理诉求','表达诉求','回应诉求'],'统筹':['统筹安排','统筹发展','加强统筹'],
 '妥善':['妥善处理','妥善安排','妥善解决'],'衔接':['做好衔接','有效衔接','衔接工作'],
 '研判':['分析研判','综合研判','研判形势'],'着力':['着力解决','着力推进','着力提高'],
}

CURATED_EXAMPLES = {
5: {
 '安慰':('朋友难过的时候，我们应该安慰他。','Khi bạn bè buồn, chúng ta nên an ủi họ.'),
 '避免':('提前检查可以避免很多错误。','Kiểm tra trước có thể tránh nhiều sai sót.'),
 '承担':('每个人都应该承担自己的责任。','Mỗi người đều nên gánh trách nhiệm của mình.'),
 '促进':('交流能够促进彼此的了解。','Giao lưu có thể thúc đẩy sự hiểu biết lẫn nhau.'),
 '独立':('孩子需要逐渐学会独立生活。','Trẻ cần dần học cách sống tự lập.'),
 '发挥':('团队合作能发挥每个人的优势。','Hợp tác nhóm giúp phát huy ưu thế của mỗi người.'),
 '反映':('这份报告反映了真实情况。','Báo cáo này phản ánh tình hình thực tế.'),
 '改善':('运动可以改善睡眠质量。','Vận động có thể cải thiện chất lượng giấc ngủ.'),
 '沟通':('遇到问题时，及时沟通很重要。','Khi gặp vấn đề, giao tiếp kịp thời rất quan trọng.'),
 '构成':('这些小问题可能构成更大的风险。','Những vấn đề nhỏ này có thể tạo thành rủi ro lớn hơn.'),
 '观察':('医生需要继续观察病人的情况。','Bác sĩ cần tiếp tục theo dõi tình trạng bệnh nhân.'),
 '规模':('这家公司正在扩大生产规模。','Công ty này đang mở rộng quy mô sản xuất.'),
 '价值':('这本书具有很高的参考价值。','Cuốn sách này có giá trị tham khảo cao.'),
 '培养':('阅读有助于培养思考能力。','Đọc sách giúp bồi dưỡng năng lực tư duy.'),
 '评价':('我们应该根据事实作出评价。','Chúng ta nên đánh giá dựa trên sự thật.'),
 '趋势':('线上学习已成为一种发展趋势。','Học trực tuyến đã trở thành một xu hướng phát triển.'),
 '确认':('请再次确认会议时间。','Vui lòng xác nhận lại thời gian họp.'),
 '申请':('他正在申请一份新的工作。','Anh ấy đang ứng tuyển một công việc mới.'),
 '实现':('只要坚持，就有机会实现目标。','Chỉ cần kiên trì thì có cơ hội thực hiện mục tiêu.'),
 '适应':('我花了一个月才适应新环境。','Tôi mất một tháng mới thích nghi với môi trường mới.'),
 '维护':('大家都有责任维护公共秩序。','Mọi người đều có trách nhiệm duy trì trật tự công cộng.'),
 '限制':('时间限制会影响我们的选择。','Giới hạn thời gian sẽ ảnh hưởng đến lựa chọn của chúng ta.'),
 '形成':('长期练习能形成良好的习惯。','Luyện tập lâu dài có thể hình thành thói quen tốt.'),
 '预防':('保持卫生有助于预防疾病。','Giữ vệ sinh giúp phòng ngừa bệnh tật.'),
 '执行':('计划制定以后，关键是认真执行。','Sau khi lập kế hoạch, điều quan trọng là thực hiện nghiêm túc.'),
},
6: {
 '挨着':('我的座位挨着窗户。','Chỗ ngồi của tôi sát cửa sổ.'),
 '颁布':('有关部门颁布了新的规定。','Cơ quan liên quan đã ban hành quy định mới.'),
 '保管':('重要文件应该由专人保管。','Tài liệu quan trọng nên do người chuyên trách bảo quản.'),
 '报酬':('他的劳动得到了合理的报酬。','Công sức của anh ấy nhận được thù lao hợp lý.'),
 '抱怨':('与其抱怨，不如想办法解决问题。','Thay vì phàn nàn, tốt hơn nên tìm cách giải quyết vấn đề.'),
 '比例':('女性员工所占的比例有所提高。','Tỷ lệ nhân viên nữ đã tăng lên.'),
 '补偿':('公司会按照规定给予补偿。','Công ty sẽ bồi thường theo quy định.'),
 '策划':('他们正在策划一场文化活动。','Họ đang lên kế hoạch cho một hoạt động văn hóa.'),
 '差距':('我们需要正视差距并继续努力。','Chúng ta cần nhìn thẳng vào khoảng cách và tiếp tục cố gắng.'),
 '撤销':('由于条件变化，原计划被撤销了。','Do điều kiện thay đổi, kế hoạch ban đầu đã bị hủy.'),
 '诚恳':('他诚恳地接受了大家的意见。','Anh ấy chân thành tiếp nhận ý kiến của mọi người.'),
 '冲突':('及时沟通可以减少不必要的冲突。','Giao tiếp kịp thời có thể giảm xung đột không cần thiết.'),
 '储备':('企业应该重视人才储备。','Doanh nghiệp nên coi trọng việc dự trữ nhân lực.'),
 '传达':('请把会议精神准确地传达下去。','Hãy truyền đạt chính xác tinh thần cuộc họp.'),
 '担保':('没有充分了解情况，不要轻易为别人担保。','Khi chưa hiểu rõ tình hình, đừng dễ dàng bảo lãnh cho người khác.'),
 '动机':('了解学习动机有助于制定计划。','Hiểu động cơ học tập giúp lập kế hoạch.'),
 '对策':('我们需要针对风险提出具体对策。','Chúng ta cần đưa ra đối sách cụ thể cho rủi ro.'),
 '风险':('投资前必须认真评估风险。','Trước khi đầu tư phải đánh giá rủi ro nghiêm túc.'),
 '贯彻':('政策能否贯彻，关键在于执行。','Chính sách có được quán triệt hay không, mấu chốt là thực hiện.'),
 '核心':('提高质量是这项工作的核心。','Nâng cao chất lượng là cốt lõi của công việc này.'),
 '监督':('整个过程应该接受社会监督。','Toàn bộ quá trình nên chịu sự giám sát của xã hội.'),
 '理念':('公司的经营理念得到了员工认同。','Triết lý kinh doanh của công ty được nhân viên đồng thuận.'),
 '评估':('项目开始前要进行全面评估。','Trước khi dự án bắt đầu cần đánh giá toàn diện.'),
 '潜力':('这个年轻人很有发展潜力。','Người trẻ này có tiềm năng phát triển lớn.'),
 '协调':('各部门需要加强协调与配合。','Các bộ phận cần tăng cường phối hợp.'),
 '需求':('产品设计必须考虑用户需求。','Thiết kế sản phẩm phải tính đến nhu cầu người dùng.'),
 '约束':('任何权力都需要受到制度约束。','Mọi quyền lực đều cần chịu sự ràng buộc của chế độ.'),
},
7: {
 '倡导':('我们倡导节约资源、保护环境。','Chúng tôi đề xướng tiết kiệm tài nguyên và bảo vệ môi trường.'),
 '遏制':('这些措施有助于遏制风险扩散。','Những biện pháp này giúp kiềm chế rủi ro lan rộng.'),
 '秉持':('企业应始终秉持诚信经营的原则。','Doanh nghiệp nên luôn giữ nguyên tắc kinh doanh thành tín.'),
 '筹措':('项目所需资金正在多方筹措。','Nguồn vốn cần cho dự án đang được huy động từ nhiều phía.'),
 '斟酌':('这句话是否合适，还需要仔细斟酌。','Câu này có phù hợp hay không vẫn cần cân nhắc kỹ.'),
 '凸显':('数据变化凸显了问题的严重性。','Biến động dữ liệu làm nổi bật mức độ nghiêm trọng của vấn đề.'),
 '诠释':('这部作品从新的角度诠释了传统文化。','Tác phẩm này diễn giải văn hóa truyền thống từ góc nhìn mới.'),
 '契机':('技术进步为行业发展带来了新契机。','Tiến bộ công nghệ mang lại thời cơ mới cho ngành.'),
 '取缔':('有关部门依法取缔了非法经营活动。','Cơ quan chức năng đã đình chỉ hoạt động kinh doanh trái phép theo pháp luật.'),
 '搁置':('由于分歧太大，讨论暂时被搁置。','Do bất đồng quá lớn, cuộc thảo luận tạm thời bị gác lại.'),
 '梳理':('我们需要先梳理问题，再确定重点。','Chúng ta cần hệ thống hóa vấn đề trước rồi xác định trọng tâm.'),
 '诉求':('有关方面应该认真回应群众的合理诉求。','Các bên liên quan nên nghiêm túc phản hồi nguyện vọng hợp lý của người dân.'),
 '推崇':('这种务实的工作作风值得推崇。','Phong cách làm việc thực tế này đáng được đề cao.'),
 '统筹':('要统筹考虑经济、社会和环境因素。','Cần cân nhắc tổng thể các yếu tố kinh tế, xã hội và môi trường.'),
 '妥善':('问题已经得到了妥善处理。','Vấn đề đã được xử lý thỏa đáng.'),
 '衔接':('新旧制度之间需要做好衔接。','Giữa chế độ mới và cũ cần làm tốt việc chuyển tiếp.'),
 '研判':('专家正在对未来形势进行分析研判。','Chuyên gia đang phân tích và đánh giá tình hình tương lai.'),
 '制约':('资源不足制约了项目的发展。','Thiếu tài nguyên đã hạn chế sự phát triển của dự án.'),
 '着力':('下一阶段要着力提高服务质量。','Giai đoạn tiếp theo cần tập trung nâng cao chất lượng dịch vụ.'),
 '涵盖':('报告涵盖了教育、医疗和就业等领域。','Báo cáo bao quát các lĩnh vực giáo dục, y tế và việc làm.'),
 '依托':('当地依托自然资源发展旅游业。','Địa phương dựa vào tài nguyên tự nhiên để phát triển du lịch.'),
 '落实':('各项措施必须落实到具体工作中。','Các biện pháp phải được triển khai vào công việc cụ thể.'),
 '规范':('需要进一步规范市场秩序。','Cần tiếp tục quy phạm hóa trật tự thị trường.'),
 '权衡':('作决定前要权衡成本与收益。','Trước khi quyết định cần cân nhắc chi phí và lợi ích.'),
 '督促':('管理人员要督促任务按时完成。','Người quản lý cần đôn đốc nhiệm vụ hoàn thành đúng hạn.'),
}
}


def py(zh: str) -> str:
    parts = lazy_pinyin(zh, style=Style.TONE, neutral_tone_with_five=False, errors=lambda x: list(x))
    out = ' '.join(parts)
    out = re.sub(r'\s+([，。！？；：、])', r'\1', out)
    return out[:1].upper() + out[1:]


def gi(code, title, formula, explanation, zh, vi, mistake):
    return {'id':code,'title':title,'formula':formula,'explanation':explanation,
            'examples':[{'zh':zh,'pinyin':py(zh),'vi':vi}],'mistake':mistake}


def grammar5():
    rows = [
('V5-01','Thay vì… chi bằng…','与其…不如…','So sánh hai lựa chọn và khuyên chọn phương án sau.','与其担心结果，不如认真准备。','Thay vì lo kết quả, chi bằng chuẩn bị nghiêm túc.','Hai vế phải là những lựa chọn có thể so sánh.'),
('V5-02','Không chỉ… mà còn…','不仅…还/而且…','Nêu quan hệ tăng tiến; vế sau bổ sung thông tin mạnh hơn.','这项工作不仅需要经验，还需要耐心。','Công việc này không chỉ cần kinh nghiệm mà còn cần kiên nhẫn.','Chú ý vị trí chủ ngữ khi hai vế cùng hoặc khác chủ ngữ.'),
('V5-03','Vừa… vừa…','既…又…','Nêu hai đặc điểm hoặc hành động cùng tồn tại.','这个办法既简单又有效。','Cách này vừa đơn giản vừa hiệu quả.','Hai thành phần nên cùng cấp ngữ pháp.'),
('V5-04','Trừ phi… mới…','除非…才…','Nêu điều kiện cần; chỉ khi điều kiện xảy ra mới có kết quả.','除非提前预约，才有可能安排时间。','Chỉ khi đặt trước mới có thể sắp xếp thời gian.','Không nhầm với 只要…就… là điều kiện đủ.'),
('V5-05','Trừ phi… nếu không…','除非…否则…','Nếu điều kiện đặc biệt không xảy ra thì kết quả sau sẽ xảy ra.','除非马上出发，否则会迟到。','Trừ khi xuất phát ngay, nếu không sẽ muộn.','否则 không đứng độc lập nếu không có điều kiện trước đó.'),
('V5-06','Bất luận… đều…','无论…都…','Kết quả không thay đổi dù điều kiện nào xảy ra.','无论遇到什么困难，我们都要坚持。','Dù gặp khó khăn gì, chúng ta đều phải kiên trì.','Sau 无论 thường cần đại từ nghi vấn hoặc các lựa chọn.'),
('V5-07','Bất kể… cũng…','不管…也/都…','Cấu trúc khẩu ngữ tương đương 无论…都….','不管别人怎么说，他都不改变决定。','Bất kể người khác nói thế nào, anh ấy cũng không đổi quyết định.','Không dùng một vế thiếu quan hệ bao quát.'),
('V5-08','Cho dù… cũng…','哪怕…也…','Nêu giả định nhượng bộ, kể cả tình huống cực đoan.','哪怕只有一点机会，也要试一试。','Cho dù chỉ có một chút cơ hội cũng phải thử.','哪怕 thường nhấn mạnh trường hợp cực đoan.'),
('V5-09','Mặc dù… nhưng…','尽管…可是/仍然…','Thừa nhận sự thật nhưng kết quả vẫn trái kỳ vọng.','尽管时间很紧，我们仍然完成了任务。','Mặc dù thời gian gấp, chúng tôi vẫn hoàn thành nhiệm vụ.','尽管 nêu sự thật, 即使 thường nêu giả định.'),
('V5-10','Sở dĩ… là vì…','之所以…是因为…','Đưa kết quả trước rồi giải thích nguyên nhân trọng tâm.','他之所以进步快，是因为每天坚持练习。','Sở dĩ anh ấy tiến bộ nhanh là vì luyện tập hằng ngày.','Không đảo sai vị trí kết quả và nguyên nhân.'),
('V5-11','Đã… thì…','既然…那么/就…','Dựa trên sự thật đã xác định để đưa kết luận.','既然已经决定了，就认真执行吧。','Đã quyết định rồi thì hãy nghiêm túc thực hiện.','Không dùng cho giả định chưa chắc xảy ra.'),
('V5-12','Hễ… là…','一…就…','Hai hành động xảy ra nối tiếp rất nhanh hoặc có quan hệ thường xuyên.','他一听到这个消息就笑了。','Anh ấy vừa nghe tin này liền cười.','Không dùng khi giữa hai hành động có khoảng cách dài không được nêu.'),
('V5-13','Một khi… thì…','一旦…就…','Nhấn mạnh khi điều kiện xảy ra thì hậu quả khó thay đổi.','一旦发现问题，就要及时处理。','Một khi phát hiện vấn đề thì phải xử lý kịp thời.','一旦 thường mang tính cảnh báo hoặc bước ngoặt.'),
('V5-14','Càng… càng…','越…越…','Mức độ hai sự việc biến đổi tương ứng.','练习得越多，表达就越自然。','Càng luyện nhiều, biểu đạt càng tự nhiên.','Nếu có hai chủ ngữ cần đặt đúng trước 越.'),
('V5-15','Cùng với…','随着 + N/V，…','Nêu sự thay đổi diễn ra cùng quá trình khác.','随着技术的发展，学习方式也在变化。','Cùng với sự phát triển công nghệ, cách học cũng thay đổi.','Sau 随着 thường là quá trình có tính thay đổi.'),
('V5-16','Đối với… mà nói','对…而言/来说，…','Giới hạn nhận xét theo một đối tượng hoặc góc nhìn.','对初学者而言，发音非常重要。','Đối với người mới học, phát âm rất quan trọng.','Không nhầm với 关于 chỉ chủ đề.'),
('V5-17','Xét từ…','从…来看，…','Đưa ra nhận xét dựa trên một phương diện hoặc dữ liệu.','从目前的情况来看，计划需要调整。','Xét tình hình hiện tại, kế hoạch cần điều chỉnh.','Cần nêu rõ căn cứ sau 从.'),
('V5-18','Có thể thấy từ…','由…可见，…','Rút kết luận từ bằng chứng trước đó.','由这些数据可见，市场需求正在增加。','Từ những dữ liệu này có thể thấy nhu cầu thị trường đang tăng.','Kết luận phải thực sự được hỗ trợ bởi bằng chứng.'),
('V5-19','Lấy… làm…','以 A 为 B','Xác lập A là mục tiêu, tiêu chuẩn hoặc cơ sở B.','我们以提高质量为主要目标。','Chúng tôi lấy nâng cao chất lượng làm mục tiêu chính.','为 sau đây mang nghĩa “làm”, không đọc giống giới từ 为了.'),
('V5-20','Coi… là…','把 A 当作 B','Xem A như B trong nhận thức hoặc cách sử dụng.','他把这次失败当作一次经验。','Anh ấy coi thất bại lần này là một kinh nghiệm.','当作 không nhất thiết nghĩa A thực sự là B.'),
('V5-21','Chịu ảnh hưởng của…','受…影响','Nêu chủ thể bị một yếu tố tác động.','受天气影响，比赛推迟了。','Do ảnh hưởng thời tiết, trận đấu bị hoãn.','Không bỏ đối tượng bị tác động nếu ngữ cảnh không rõ.'),
('V5-22','Gây ảnh hưởng đến…','对…产生影响','Nêu một yếu tố tạo tác động lên đối tượng.','生活习惯会对健康产生影响。','Thói quen sống sẽ gây ảnh hưởng đến sức khỏe.','Phân biệt với 受到影响 là phía chịu tác động.'),
('V5-23','Khiến cho với 使得','A 使得 B + V/Adj','A dẫn đến trạng thái hoặc kết quả của B.','新的方法使得工作效率明显提高。','Phương pháp mới khiến hiệu suất công việc tăng rõ rệt.','使得 thường trang trọng hơn 让.'),
('V5-24','Để tiện…','…，以便…','Nêu mục đích tạo điều kiện thuận lợi cho hành động sau.','请记录重点，以便以后复习。','Hãy ghi lại trọng điểm để tiện ôn sau này.','以便 thường nối mục đích, không phải kết quả đã xảy ra.'),
('V5-25','Để khỏi…','…，免得/省得…','Nêu hành động nhằm tránh kết quả không mong muốn.','提前出发，免得路上堵车。','Xuất phát sớm để khỏi gặp tắc đường.','Vế sau thường là điều tiêu cực muốn tránh.'),
('V5-26','Khó tránh khỏi','难免 + V/Adj','Nói một tình huống khó hoàn toàn tránh được.','第一次做这项工作，难免会出错。','Lần đầu làm công việc này khó tránh khỏi sai sót.','难免 không có nghĩa chắc chắn luôn xảy ra.'),
('V5-27','Chưa chắc','未必 + V/Adj','Phủ định khả năng chắc chắn, tương đương “không hẳn”.','经验多的人未必适合管理。','Người nhiều kinh nghiệm chưa chắc phù hợp quản lý.','未必 không đồng nghĩa với 一定不.'),
('V5-28','Buộc phải','不得不 + V','Không có lựa chọn khác ngoài thực hiện hành động.','由于时间不够，我们不得不改变计划。','Do không đủ thời gian, chúng tôi buộc phải đổi kế hoạch.','Sắc thái bị hoàn cảnh ép buộc mạnh hơn 必须.'),
('V5-29','Không nhịn được','忍不住 + V','Không kiểm soát được phản ứng hoặc hành động.','听到这个好消息，她忍不住笑了。','Nghe tin tốt này, cô ấy không nhịn được cười.','Sau 忍不住 là hành động thực tế phát sinh.'),
('V5-30','Không kịp','来不及 + V','Không đủ thời gian để hoàn thành hành động.','快一点，不然来不及上车了。','Nhanh lên, nếu không sẽ không kịp lên xe.','Phân biệt với 没来得及 là đã không kịp trong quá khứ.'),
('V5-31','Kịp/không kịp tiến độ','赶得上/赶不上 + N','Có hoặc không theo kịp thời gian, chuyến xe hay tiến độ.','现在出发还赶得上最后一班车。','Xuất phát bây giờ vẫn kịp chuyến cuối.','赶上 còn có nghĩa gặp đúng lúc; cần theo ngữ cảnh.'),
('V5-32','Coi như là','算是 + N/Adj','Đưa ra đánh giá tương đối hoặc miễn cưỡng công nhận.','这次结果算是比较理想。','Kết quả lần này coi như khá lý tưởng.','算是 thường giảm mức độ khẳng định.'),
('V5-33','Quả thực đến mức…','简直 + V/Adj','Nhấn mạnh mức độ rất cao, thường có cảm xúc.','这里的变化简直让人不敢相信。','Sự thay đổi ở đây quả thực khiến người ta khó tin.','Tránh dùng trong văn phong cần hoàn toàn trung tính.'),
('V5-34','Dù sao thì','毕竟 + mệnh đề','Nêu sự thật quan trọng cần được tính đến.','他毕竟是第一次参加这种比赛。','Dù sao đây cũng là lần đầu anh ấy tham gia cuộc thi như vậy.','毕竟 thường giải thích hoặc điều chỉnh đánh giá trước đó.'),
('V5-35','Huống hồ','何况 + mệnh đề','Đưa trường hợp mạnh hơn để củng cố kết luận.','这么简单的问题他都懂，何况你呢？','Vấn đề đơn giản vậy anh ấy còn hiểu, huống hồ là bạn.','Phần sau phải dễ kết luận hơn dựa trên phần trước.'),
('V5-36','Hơn nữa','况且 + mệnh đề','Bổ sung thêm lý do cùng hướng.','时间还早，况且路也不远。','Thời gian còn sớm, hơn nữa đường cũng không xa.','况且 không dùng để biểu thị đối lập.'),
('V5-37','Dù thế nào cũng…','反正 + mệnh đề','Nêu kết luận không thay đổi dù tình huống cụ thể thế nào.','反正已经来了，就进去看看吧。','Dù sao cũng đã đến rồi, hãy vào xem thử.','Có sắc thái khẩu ngữ, đôi khi thể hiện không quan tâm chi tiết.'),
('V5-38','Tóm lại','总之，…','Tổng kết nhiều thông tin thành kết luận chung.','总之，我们需要先解决最重要的问题。','Tóm lại, chúng ta cần giải quyết vấn đề quan trọng nhất trước.','Nên dùng sau khi đã có căn cứ hoặc phân tích.'),
('V5-39','Còn về…','至于 + N，…','Chuyển sang chủ đề liên quan nhưng tách biệt.','至于具体时间，我们以后再商量。','Còn thời gian cụ thể, chúng ta sẽ bàn sau.','Không dùng 至于 khi muốn nêu nguyên nhân.'),
('V5-40','Cố gắng hết mức','尽量 + V','Thực hiện hành động trong phạm vi khả năng lớn nhất.','请尽量提前完成这项工作。','Hãy cố gắng hoàn thành công việc này sớm.','尽量 không đồng nghĩa với 一定.'),
('V5-41','Khá, tương đối','相当 + Adj','Nhấn mạnh mức độ tương đối cao.','这个任务相当复杂。','Nhiệm vụ này khá phức tạp.','相当于 là “tương đương với”, khác 相当 + tính từ.'),
('V5-42','Cái gọi là…','所谓 + N','Giới thiệu hoặc bình luận về một khái niệm được gọi tên.','所谓经验，就是从实践中得到的认识。','Cái gọi là kinh nghiệm chính là nhận thức có được từ thực tiễn.','Có thể mang sắc thái trung tính hoặc hoài nghi tùy ngữ cảnh.'),
('V5-43','Lần lượt','分别 + V','Các chủ thể hoặc đối tượng thực hiện riêng từng hành động.','三位代表分别介绍了自己的方案。','Ba đại diện lần lượt giới thiệu phương án của mình.','Không dùng khi mọi người cùng thực hiện một hành động chung.'),
('V5-44','Dần từng bước','逐步 + V','Quá trình thay đổi theo các bước có tổ chức.','我们将逐步完善管理制度。','Chúng tôi sẽ từng bước hoàn thiện chế độ quản lý.','逐步 thiên về các bước; 逐渐 thiên về biến đổi theo thời gian.'),
('V5-45','Kể cả, thậm chí','甚至 + mệnh đề','Đưa trường hợp cao hơn hoặc bất ngờ hơn.','他忙得甚至没有时间吃饭。','Anh ấy bận đến mức thậm chí không có thời gian ăn.','Thông tin sau 甚至 phải tăng tiến rõ.'),
]
    return [gi(*r) for r in rows]


def grammar6():
    rows = [
('V6-01','Nói là… chi bằng nói là…','与其说 A，不如说 B','Điều chỉnh cách diễn đạt: B chính xác hơn A.','与其说他运气好，不如说他准备得充分。','Nói anh ấy may mắn chi bằng nói anh ấy chuẩn bị đầy đủ.','A và B phải cùng giải thích một hiện tượng.'),
('V6-02','Không phải… mà là…','不是 A，而是 B','Bác bỏ A và xác nhận B.','问题不是缺少机会，而是缺少准备。','Vấn đề không phải thiếu cơ hội mà là thiếu chuẩn bị.','Hai vế nên cùng cấp ngữ pháp.'),
('V6-03','Thà… chứ không…','宁可 A，也不 B','Chọn A dù bất lợi để tránh B.','我宁可多花时间，也不降低质量。','Tôi thà tốn thêm thời gian chứ không giảm chất lượng.','Không dùng khi hai lựa chọn không có quan hệ ưu tiên.'),
('V6-04','Chỉ có điều','只不过 + mệnh đề','Bổ sung hạn chế nhỏ hoặc làm nhẹ sự khác biệt.','办法是可行的，只不过成本有点高。','Cách này khả thi, chỉ có điều chi phí hơi cao.','只不过 không phủ định toàn bộ vế trước.'),
('V6-05','Chẳng qua chỉ là','无非是/无非 + V','Thu hẹp bản chất sự việc về một nguyên nhân hoặc loại đơn giản.','他这样做无非是想证明自己。','Anh ấy làm vậy chẳng qua là muốn chứng minh bản thân.','Có thể mang sắc thái coi nhẹ; dùng thận trọng.'),
('V6-06','Giả sử','倘若/假如…，就…','Đưa điều kiện giả định, thường dùng trong văn viết.','倘若情况发生变化，我们就调整方案。','Nếu tình hình thay đổi, chúng ta sẽ điều chỉnh phương án.','Không dùng như sự thật đã xác định.'),
('V6-07','Dù cho','即便…，也…','Giả định nhượng bộ; kết quả không đổi.','即便遇到反对意见，也要耐心解释。','Dù gặp ý kiến phản đối cũng phải kiên nhẫn giải thích.','即便 thường giả định, 尽管 thường thừa nhận sự thật.'),
('V6-08','Mặc dù vậy','尽管如此，…','Chuyển từ hoàn cảnh bất lợi sang kết quả vẫn tiếp tục.','准备时间很短，尽管如此，我们还是完成了任务。','Thời gian chuẩn bị ngắn, mặc dù vậy chúng tôi vẫn hoàn thành nhiệm vụ.','如此 thay cho toàn bộ tình huống trước.'),
('V6-09','Đến mức','以至于 + kết quả','Nêu kết quả phát triển đến mức độ cao, thường ngoài dự kiến.','雨下得太大，以至于交通完全中断。','Mưa quá lớn đến mức giao thông hoàn toàn gián đoạn.','Vế trước phải đủ mạnh để dẫn đến kết quả.'),
('V6-10','Để tránh','以免 + kết quả xấu','Nêu mục đích tránh hậu quả không mong muốn.','请提前确认，以免出现误会。','Hãy xác nhận trước để tránh hiểu lầm.','Sau 以免 thường là kết quả tiêu cực chưa xảy ra.'),
('V6-11','Đến nỗi gây ra','以致 + kết quả','Nêu kết quả thực tế, thường tiêu cực.','他忽视了细节，以致造成严重损失。','Anh ấy bỏ qua chi tiết, đến nỗi gây tổn thất nghiêm trọng.','Khác 以免 là mục đích phòng tránh.'),
('V6-12','Vì thế','因而 + mệnh đề','Nối nguyên nhân với kết quả theo văn viết.','市场需求增加，因而产量也有所提高。','Nhu cầu thị trường tăng, vì thế sản lượng cũng tăng.','Không dùng khi hai vế không có quan hệ nguyên nhân.'),
('V6-13','Nhờ đó, từ đó','从而 + mệnh đề','Nêu kết quả đạt được thông qua hành động trước.','我们改进了流程，从而提高了效率。','Chúng tôi cải tiến quy trình, từ đó nâng hiệu suất.','从而 thiên về kết quả logic, không đơn thuần là trình tự thời gian.'),
('V6-14','Xét vì','鉴于 + tình hình','Nêu căn cứ dẫn đến quyết định, văn phong trang trọng.','鉴于天气恶劣，活动将延期举行。','Xét vì thời tiết xấu, hoạt động sẽ hoãn.','Sau 鉴于 là căn cứ đã biết.'),
('V6-15','Nhắm vào','针对 + đối tượng + V','Hành động được thiết kế cho vấn đề hoặc nhóm cụ thể.','我们针对主要问题提出了三项措施。','Chúng tôi đưa ra ba biện pháp nhắm vào vấn đề chính.','针对 không đồng nghĩa hoàn toàn với 关于.'),
('V6-16','Xét về…','就…而言，…','Giới hạn nhận xét ở một phương diện.','就长期效果而言，这个办法更可靠。','Xét về hiệu quả dài hạn, cách này đáng tin hơn.','Cần nêu rõ phương diện giữa 就 và 而言.'),
('V6-17','Từ góc độ…','从…角度看，…','Phân tích theo một góc nhìn xác định.','从用户角度看，操作还不够方便。','Từ góc độ người dùng, thao tác vẫn chưa đủ thuận tiện.','Kết luận có thể thay đổi theo góc nhìn khác.'),
('V6-18','Trên cơ sở…','在…基础上 + V','Hành động mới dựa trên thành quả hoặc điều kiện sẵn có.','我们将在调查基础上完善方案。','Chúng tôi sẽ hoàn thiện phương án trên cơ sở khảo sát.','基础 phải là căn cứ thực chất.'),
('V6-19','Với điều kiện tiên quyết…','在…前提下 + V','Chỉ hành động khi điều kiện nền tảng được bảo đảm.','在保证安全的前提下，可以提高速度。','Với điều kiện bảo đảm an toàn, có thể tăng tốc độ.','Không nhầm với 条件下 chỉ điều kiện nói chung.'),
('V6-20','Trong phạm vi…','在…范围内 + V','Giới hạn hành động hoặc kết luận trong một phạm vi.','问题必须在法律范围内解决。','Vấn đề phải được giải quyết trong phạm vi pháp luật.','Phạm vi cần được nêu cụ thể.'),
('V6-21','Từ đó xem ra','由此看来，…','Rút ra đánh giá từ sự việc hoặc bằng chứng trước.','由此看来，原来的判断需要修改。','Từ đó xem ra, phán đoán ban đầu cần sửa đổi.','Không rút kết luận vượt quá bằng chứng.'),
('V6-22','Có thể thấy','可见 + mệnh đề','Đưa kết luận rõ từ thông tin đã nêu.','他每天坚持记录，可见他非常重视这件事。','Anh ấy ghi chép mỗi ngày, có thể thấy rất coi trọng việc này.','可见 không phải nghĩa nhìn thấy trực tiếp trong cấu trúc này.'),
('V6-23','Theo dữ liệu…','据…显示/表明，…','Dẫn nguồn thông tin làm căn cứ.','据调查显示，多数用户支持这一变化。','Theo khảo sát, đa số người dùng ủng hộ thay đổi này.','Tránh dùng 据 và 根据 chồng chéo không cần thiết.'),
('V6-24','Nghe nói','据说 + mệnh đề','Truyền đạt thông tin chưa trực tiếp xác nhận.','据说这个项目下个月开始。','Nghe nói dự án này bắt đầu tháng sau.','Không trình bày 据说 như sự thật đã xác minh.'),
('V6-25','Không phải là','并非 + mệnh đề','Phủ định trang trọng, thường sửa hiểu lầm.','结果并非完全由运气决定。','Kết quả không hoàn toàn do may mắn quyết định.','并非 không nhất thiết phủ định mọi phần sau.'),
('V6-26','Hơi quá, không khỏi','未免 + Adj/V','Đánh giá một tình trạng vượt mức hợp lý.','这样的要求未免太严格了。','Yêu cầu như vậy có phần quá nghiêm khắc.','Thường mang thái độ phê bình nhẹ.'),
('V6-27','Không khỏi','不免 + V','Một phản ứng hoặc kết quả tự nhiên khó tránh.','看到这些变化，人们不免感到担心。','Thấy những thay đổi này, người ta không khỏi lo lắng.','Không nhầm với 难免 thiên về khả năng khó tránh.'),
('V6-28','Làm sao lại không…','何尝不/何尝不是…','Câu hỏi tu từ khẳng định điều bị hỏi.','我何尝不想早点完成，只是条件不允许。','Tôi đâu phải không muốn hoàn thành sớm, chỉ là điều kiện không cho phép.','Cần hiểu theo nghĩa khẳng định ngược.'),
('V6-29','Chẳng lẽ','莫非 + mệnh đề nghi vấn','Đưa suy đoán có sắc thái ngạc nhiên hoặc nghi ngờ.','这么晚还没回来，莫非遇到麻烦了？','Muộn vậy chưa về, chẳng lẽ gặp rắc rối?','Không dùng như câu trần thuật chắc chắn.'),
('V6-30','Dù thế nào','无论如何 + mệnh đề','Kết luận hoặc ý chí không thay đổi trong mọi trường hợp.','无论如何，我们都不能放弃原则。','Dù thế nào, chúng ta cũng không thể từ bỏ nguyên tắc.','Có sắc thái mạnh, không dùng cho lựa chọn nhỏ.'),
('V6-31','Ngược lại','反之，…','Nêu kết quả đối nghịch nếu điều kiện đảo ngược.','准备充分会提高成功率，反之则容易失败。','Chuẩn bị đầy đủ tăng tỷ lệ thành công, ngược lại dễ thất bại.','Phải có quan hệ đảo ngược logic rõ.'),
('V6-32','Đồng thời','与此同时，…','Nêu sự việc khác xảy ra cùng lúc hoặc song song.','成本下降了，与此同时，质量也提高了。','Chi phí giảm, đồng thời chất lượng cũng tăng.','Không nhất thiết là quan hệ nguyên nhân.'),
('V6-33','So sánh ra thì','相比之下，…','Làm nổi bật sự khác biệt sau khi so sánh.','旧方案成本较高，相比之下，新方案更灵活。','Phương án cũ chi phí cao; so ra phương án mới linh hoạt hơn.','Cần có đối tượng so sánh trước đó.'),
('V6-34','Nói cách khác','换句话说，…','Diễn đạt lại nội dung bằng cách dễ hiểu hoặc chính xác hơn.','资源有限，换句话说，我们必须作出选择。','Tài nguyên có hạn, nói cách khác chúng ta phải lựa chọn.','Không thêm ý mới trái với câu trước.'),
('V6-35','Nói chính xác','确切地说，…','Sửa hoặc tinh chỉnh phát biểu trước cho chính xác hơn.','他不是拒绝，确切地说，他还没有决定。','Anh ấy không phải từ chối; nói chính xác là chưa quyết định.','Dùng khi nội dung sau chính xác hơn, không chỉ lặp lại.'),
('V6-36','Nói chung','总而言之，…','Tổng hợp lập luận thành kết luận cuối.','总而言之，这个方案值得进一步研究。','Nói chung, phương án này đáng nghiên cứu thêm.','Phù hợp văn viết hơn 总之.'),
('V6-37','Một mặt… mặt khác…','一方面…另一方面…','Phân tích hai phương diện song song.','一方面要控制成本，另一方面要保证质量。','Một mặt phải kiểm soát chi phí, mặt khác bảo đảm chất lượng.','Hai mặt có thể bổ sung hoặc đối lập.'),
('V6-38','Vừa… cũng…','既…也…','Nêu hai đặc điểm hoặc yêu cầu đồng thời.','管理既要严格，也要有耐心。','Quản lý vừa phải nghiêm, cũng phải kiên nhẫn.','Hai thành phần nên cùng cấu trúc.'),
('V6-39','Một là… hai là…','一来…二来…','Nêu hai lý do hoặc lợi ích.','我选择这里，一来交通方便，二来环境安静。','Tôi chọn nơi này, một là giao thông thuận tiện, hai là môi trường yên tĩnh.','Thường dùng đúng hai lý do chính.'),
('V6-40','Trình tự lập luận','首先…其次…最后…','Tổ chức nhiều bước hoặc luận điểm theo thứ tự.','首先分析原因，其次提出对策，最后确定计划。','Trước hết phân tích nguyên nhân, tiếp theo đề xuất đối sách, cuối cùng xác định kế hoạch.','Mỗi bước cần cùng cấp độ logic.'),
('V6-41','Các loại như…','…之类','Chỉ một nhóm sự vật tương tự ví dụ trước.','报告、合同之类的文件要分类保管。','Các tài liệu như báo cáo, hợp đồng cần được phân loại bảo quản.','之类 đặt sau ví dụ đại diện.'),
('V6-42','Cho đến, thậm chí','乃至 + N/V','Mở rộng phạm vi đến mức cao hơn.','这个变化影响了个人、企业乃至整个行业。','Thay đổi này ảnh hưởng cá nhân, doanh nghiệp, thậm chí cả ngành.','Các thành phần phải có thứ tự tăng tiến.'),
('V6-43','Ban cho, tiến hành','予以 + V/N','Cách diễn đạt trang trọng: thực hiện một xử lý đối với đối tượng.','对合理建议应当予以采纳。','Nên tiếp thu những kiến nghị hợp lý.','予以 thường đi với động từ hai âm tiết như 支持、处理、确认.'),
('V6-44','Tiến hành, áp dụng','加以 + V','Thực hiện hành động xử lý lên nội dung trước.','发现问题以后要及时加以解决。','Sau khi phát hiện vấn đề phải kịp thời giải quyết.','Không dùng với mọi động từ đơn giản trong khẩu ngữ.'),
('V6-45','Có thể nhờ đó','得以 + V','Nhờ điều kiện nào đó mà hành động có thể thực hiện.','在大家的帮助下，项目得以顺利完成。','Nhờ mọi người giúp đỡ, dự án đã có thể hoàn thành thuận lợi.','Thường dùng trong văn viết và cần nguyên nhân thuận lợi.'),
('V6-46','Còn chờ được…','有待 + V','Một vấn đề chưa hoàn tất, cần tiếp tục xử lý hoặc kiểm chứng.','这个结论还有待进一步验证。','Kết luận này còn cần được kiểm chứng thêm.','Không dùng cho việc đã hoàn thành.'),
('V6-47','Chắc chắn sẽ','势必 + V','Dự đoán kết quả khó tránh do xu thế hoặc nguyên nhân mạnh.','忽视质量势必影响长期发展。','Bỏ qua chất lượng chắc chắn sẽ ảnh hưởng phát triển dài hạn.','Mức khẳng định mạnh; cần căn cứ rõ.'),
('V6-48','Đặc biệt là','尤其是 + N/V','Nêu thành phần nổi bật trong phạm vi trước.','很多因素会影响结果，尤其是准备程度。','Nhiều yếu tố ảnh hưởng kết quả, đặc biệt là mức độ chuẩn bị.','Phần sau phải thuộc nhóm trước.'),
('V6-49','Thậm chí','甚至 + V/N','Đưa trường hợp cực đoan hơn.','问题影响了工作，甚至影响了正常生活。','Vấn đề ảnh hưởng công việc, thậm chí cuộc sống bình thường.','Cần sắp xếp tăng tiến.'),
('V6-50','Vân vân','…等等','Kết thúc danh sách chưa liệt kê hết.','成本、时间、风险等等都需要考虑。','Chi phí, thời gian, rủi ro v.v. đều cần cân nhắc.','Không lặp 等等 sau 之类 một cách dư thừa.'),
]
    return [gi(*r) for r in rows]


def grammar7():
    rows = [
('V7-01','Không ngại thử','不妨 + V','Đưa ra đề nghị nhẹ nhàng: có thể thử làm.','遇到困难时，不妨换一个角度思考。','Khi gặp khó khăn, có thể thử suy nghĩ từ góc độ khác.','Không mang nghĩa bắt buộc.'),
('V7-02','Không đến mức','不至于 + V/Adj','Phủ định hậu quả hoặc mức độ quá nghiêm trọng.','一次失败还不至于让整个计划停止。','Một lần thất bại chưa đến mức khiến cả kế hoạch dừng lại.','Không dùng để phủ định hoàn toàn khả năng.'),
('V7-03','Chưa chắc','不见得 + mệnh đề','Bày tỏ nghi ngờ về một phán đoán.','投入越多，效果不见得越好。','Đầu tư càng nhiều, hiệu quả chưa chắc càng tốt.','Không đồng nghĩa với chắc chắn sai.'),
('V7-04','Cũng không phải không thể','未尝不可','Công nhận một phương án có thể thử hoặc chấp nhận.','在条件允许的情况下，推迟一周未尝不可。','Khi điều kiện cho phép, hoãn một tuần cũng không phải không thể.','Sắc thái dè dặt, không phải đồng ý mạnh.'),
('V7-05','Không có gì đáng trách','无可厚非','Công nhận hành động có lý do và không nên chỉ trích quá mức.','他首先考虑家庭利益，这本身无可厚非。','Anh ấy ưu tiên lợi ích gia đình, bản thân điều đó không có gì đáng trách.','Không có nghĩa hành động hoàn toàn đúng trong mọi mặt.'),
('V7-06','Không cần nghi ngờ','毋庸置疑','Khẳng định mạnh một sự thật rõ ràng.','毋庸置疑，数据质量会影响最终结论。','Không cần nghi ngờ, chất lượng dữ liệu ảnh hưởng kết luận cuối.','Chỉ dùng khi có căn cứ vững chắc.'),
('V7-07','Có thể tưởng tượng','可想而知','Kết quả hiển nhiên có thể suy ra.','缺乏准备的后果可想而知。','Hậu quả của việc thiếu chuẩn bị có thể tưởng tượng được.','Thường thay cho kết quả tiêu cực/đáng kể không cần nói hết.'),
('V7-08','Không nói cũng rõ','不言而喻','Ý nghĩa hoặc kết luận quá rõ không cần giải thích.','诚信对企业的重要性不言而喻。','Tầm quan trọng của thành tín đối với doanh nghiệp không nói cũng rõ.','Tránh dùng khi kết luận còn tranh cãi.'),
('V7-09','Không thể tránh khỏi','不可避免','Một kết quả chắc chắn khó loại bỏ hoàn toàn.','改革过程中出现一些困难是不可避免的。','Xuất hiện một số khó khăn trong quá trình cải cách là không thể tránh khỏi.','Không dùng để biện minh cho sai sót có thể phòng tránh.'),
('V7-10','Bất luận có… hay không','无论…与否，都…','Kết quả không đổi dù trạng thái có hay không.','无论计划能否通过，我们都要做好准备。','Dù kế hoạch có được thông qua hay không, chúng ta đều phải chuẩn bị.','与否 đi sau động từ/tính từ hai khả năng.'),
('V7-11','Thay vì… chi bằng…','与其…倒不如…','Đưa lời khuyên mạnh hơn chọn vế sau.','与其不断争论，倒不如先收集证据。','Thay vì tranh luận mãi, chi bằng thu thập bằng chứng trước.','倒 làm tăng sắc thái chuyển hướng.'),
('V7-12','Dẫu… vẫn…','纵然…也…','Nhượng bộ giả định mang sắc thái văn viết.','纵然条件有限，我们也不能降低标准。','Dẫu điều kiện hạn chế, chúng ta cũng không thể hạ tiêu chuẩn.','纵然 trang trọng hơn 即使.'),
('V7-13','Dù vậy','即便如此，…','Thừa nhận toàn bộ tình huống trước nhưng kết luận vẫn khác.','风险已经降低，即便如此，仍需持续监督。','Rủi ro đã giảm, dù vậy vẫn cần giám sát liên tục.','如此 phải có nội dung trước để thay thế.'),
('V7-14','Tạm thời cứ…','姑且 + V','Chấp nhận hoặc làm tạm một phương án chưa hoàn hảo.','证据还不充分，我们姑且保留这个判断。','Bằng chứng chưa đủ, chúng ta tạm giữ phán đoán này.','Có sắc thái tạm thời, không phải kết luận cuối.'),
('V7-15','Ngay cả… huống hồ…','尚且…何况…','Từ trường hợp đã khó/đúng suy ra trường hợp mạnh hơn.','专业人员尚且需要核实，何况普通读者。','Người chuyên môn còn cần kiểm tra, huống hồ độc giả bình thường.','Quan hệ mức độ phải hợp logic.'),
('V7-16','Một là… hai là…','一则…二则…','Liệt kê hai lý do trong văn viết.','选择这个方案，一则成本较低，二则风险可控。','Chọn phương án này, một là chi phí thấp, hai là rủi ro kiểm soát được.','Thường dùng đúng hai lý do chính.'),
('V7-17','Thứ nhất… thứ hai…','其一…其二…','Phân chia hai luận điểm hoặc nguyên nhân.','问题有两个方面：其一是资金，其二是人才。','Vấn đề có hai mặt: thứ nhất là vốn, thứ hai là nhân lực.','Cấu trúc dùng trong trình bày có tổ chức.'),
('V7-18','Vừa phải… vừa phải…','既要…又要…','Hai mục tiêu hoặc yêu cầu phải đồng thời đạt.','发展经济既要重视速度，又要保证质量。','Phát triển kinh tế vừa phải coi trọng tốc độ vừa bảo đảm chất lượng.','Hai vế nên cân đối.'),
('V7-19','Cố nhiên… nhưng…','固然…但是…','Công nhận điều đúng trước rồi bổ sung giới hạn hoặc phản biện.','经验固然重要，但是学习能力同样关键。','Kinh nghiệm cố nhiên quan trọng, nhưng năng lực học cũng then chốt.','固然 thường dẫn điều được công nhận.'),
('V7-20','Quả thật… tuy nhiên…','诚然…然而…','Công nhận luận điểm rồi chuyển sang ý đối lập trong văn viết.','诚然，技术提高了效率，然而也带来了新风险。','Quả thật công nghệ tăng hiệu suất, tuy nhiên cũng mang rủi ro mới.','Phù hợp lập luận trang trọng.'),
('V7-21','Mặc dù… vẫn…','尽管…仍然…','Nhấn mạnh kết quả vẫn duy trì bất chấp trở ngại thực tế.','尽管争议不断，改革仍然在推进。','Mặc dù tranh cãi liên tục, cải cách vẫn tiến triển.','尽管 nêu sự thật, không phải giả định thuần túy.'),
('V7-22','Trừ phi… nếu không…','除非…不然…','Điều kiện duy nhất để tránh kết quả sau.','除非及时调整，不然问题会进一步扩大。','Trừ khi điều chỉnh kịp thời, nếu không vấn đề sẽ mở rộng.','不然 tương đương 否则, khẩu ngữ hơn.'),
('V7-23','Chỉ cần… là…','只要…便…','Điều kiện đủ dẫn đến kết quả, văn viết hơn 就.','只要证据充分，便可以作出判断。','Chỉ cần bằng chứng đầy đủ là có thể phán đoán.','Không nhầm với 只有…才….'),
('V7-24','Một khi… thì…','一旦…便…','Kết quả xảy ra ngay khi điều kiện quan trọng xuất hiện.','一旦制度失去约束，便可能产生风险。','Một khi chế độ mất ràng buộc thì có thể phát sinh rủi ro.','Thường nói hậu quả khó đảo ngược.'),
('V7-25','Chỉ có… mới…','唯有…才…','Nhấn mạnh điều kiện hoặc con đường duy nhất.','唯有持续学习，才不会被变化淘汰。','Chỉ có học liên tục mới không bị thay đổi đào thải.','Sắc thái mạnh hơn 只有.'),
('V7-26','Hễ là… đều…','凡是…都…','Khái quát mọi đối tượng thuộc phạm vi.','凡是涉及安全的问题都必须认真处理。','Mọi vấn đề liên quan an toàn đều phải xử lý nghiêm túc.','Tránh khái quát quá mức nếu có ngoại lệ.'),
('V7-27','Mỗi khi… liền…','每逢…便…','Sự việc lặp lại vào một dịp hoặc điều kiện.','每逢年末，公司便会总结全年工作。','Mỗi dịp cuối năm, công ty sẽ tổng kết công việc cả năm.','每逢 thường đi với dịp lặp định kỳ.'),
('V7-28','Tính đến…','截至 + thời điểm','Xác định giới hạn thời gian của số liệu hoặc tiến độ.','截至今年六月，项目已完成百分之八十。','Tính đến tháng sáu năm nay, dự án đã hoàn thành 80%.','Không dùng cho điểm bắt đầu; điểm bắt đầu dùng 自/从.'),
('V7-29','Kể từ… đến nay','自…以来','Khoảng thời gian bắt đầu từ một mốc và kéo dài đến hiện tại/điểm quy chiếu.','自政策实施以来，情况明显改善。','Kể từ khi chính sách được thực hiện, tình hình cải thiện rõ.','Vế sau thường là thay đổi hoặc trạng thái kéo dài.'),
('V7-30','Dựa trên','基于 + căn cứ','Đưa ra hành động hoặc kết luận trên một nền tảng.','该结论是基于长期调查得出的。','Kết luận này được đưa ra dựa trên khảo sát dài hạn.','Căn cứ phải được nêu rõ, tránh dùng mơ hồ.'),
('V7-31','Với tinh thần/nguyên tắc','本着 + nguyên tắc + V','Hành động theo một mục đích hoặc nguyên tắc cơ bản.','我们本着实事求是的原则处理问题。','Chúng tôi xử lý vấn đề theo nguyên tắc tôn trọng sự thật.','Thường dùng trong văn bản trang trọng.'),
('V7-32','Xoay quanh','围绕 + chủ đề + V','Tổ chức hoạt động tập trung vào một chủ đề trung tâm.','会议围绕质量管理展开讨论。','Cuộc họp thảo luận xoay quanh quản lý chất lượng.','Không nhầm với 周围 chỉ không gian xung quanh.'),
('V7-33','Nhắm vào','针对 + đối tượng + V','Đưa biện pháp có mục tiêu cụ thể.','针对存在的问题，专家提出了改进建议。','Nhằm vào các vấn đề tồn tại, chuyên gia đưa kiến nghị cải tiến.','Đối tượng sau 针对 phải rõ.'),
('V7-34','Xét vì','鉴于 + tình hình','Đưa căn cứ trang trọng cho quyết định.','鉴于风险尚未消除，项目暂缓启动。','Xét vì rủi ro chưa được loại bỏ, dự án tạm hoãn khởi động.','Không dùng cho nguyên nhân cảm xúc thông thường.'),
('V7-35','Xét điều này','有鉴于此，…','Dựa trên toàn bộ thông tin trước để đưa quyết định.','市场变化很快，有鉴于此，我们必须及时调整。','Thị trường thay đổi nhanh; xét điều này, chúng ta phải điều chỉnh kịp thời.','此 thay cho căn cứ đã nêu trước.'),
('V7-36','Về việc này','就此 + V','Hành động hoặc phát biểu liên quan trực tiếp nội dung vừa nêu.','双方将就此展开进一步谈判。','Hai bên sẽ tiến hành đàm phán thêm về việc này.','就此 có thể nghĩa “từ đây kết thúc” tùy động từ.'),
('V7-37','Nhân đây','借此 + V','Tận dụng cơ hội/sự việc này để làm điều khác.','我想借此机会感谢所有参与者。','Tôi muốn nhân cơ hội này cảm ơn mọi người tham gia.','借此 phải có cơ hội hoặc phương tiện trước.'),
('V7-38','Từ đó','由此 + V/结论','Nêu kết quả hoặc điểm xuất phát từ nội dung trước.','由此产生的成本需要重新评估。','Chi phí phát sinh từ đó cần được đánh giá lại.','由此 có thể nối danh từ hoặc kết luận.'),
('V7-39','Từ đó có thể thấy','由此可见，…','Rút kết luận rõ từ bằng chứng.','由此可见，单一措施难以解决复杂问题。','Từ đó có thể thấy, một biện pháp đơn lẻ khó giải quyết vấn đề phức tạp.','Không suy diễn vượt dữ liệu.'),
('V7-40','Xét đến cùng','归根结底，…','Nêu nguyên nhân hoặc bản chất cuối cùng.','归根结底，竞争力来自持续创新。','Xét đến cùng, năng lực cạnh tranh đến từ đổi mới liên tục.','Dùng ở kết luận bản chất, không thay cho nguyên nhân trực tiếp.'),
('V7-41','Theo một nghĩa nào đó','从某种意义上说，…','Đưa nhận xét đúng trong một phạm vi diễn giải.','从某种意义上说，失败也是一种资源。','Theo một nghĩa nào đó, thất bại cũng là một nguồn lực.','Cụm này giới hạn mức khẳng định, không chứng minh luận điểm.'),
('V7-42','Ở mức độ lớn','在很大程度上','Nêu tác động hoặc mức đúng khá cao nhưng không tuyệt đối.','结果在很大程度上取决于执行质量。','Kết quả phần lớn phụ thuộc chất lượng thực hiện.','Không đồng nghĩa hoàn toàn với 完全.'),
('V7-43','So sánh ra','相形之下，…','Qua đối chiếu, một bên hiện rõ hơn về đặc điểm.','传统方法成本较高，相形之下，新方法更灵活。','Phương pháp truyền thống chi phí cao; so ra phương pháp mới linh hoạt hơn.','Cần có hai đối tượng so sánh.'),
('V7-44','Nhìn ngược lại','反观 + đối tượng','Chuyển sang xem xét đối tượng trái ngược để so sánh.','反观另一组数据，变化并不明显。','Nhìn ngược lại nhóm dữ liệu kia, thay đổi không rõ.','Thường dùng trong lập luận so sánh.'),
('V7-45','Tiến thêm một bước','进而 + V','Kết quả hoặc hành động phát triển thêm từ bước trước.','先改善流程，进而提高整体效率。','Trước hết cải thiện quy trình, tiến tới nâng hiệu suất tổng thể.','Hai bước phải có quan hệ phát triển logic.'),
('V7-46','Tiếp đó','继而 + V','Hành động tiếp nối theo trình tự tương đối trang trọng.','双方先交换意见，继而讨论合作细节。','Hai bên trước trao đổi ý kiến, tiếp đó thảo luận chi tiết hợp tác.','继而 thiên về trình tự, 进而 thiên về phát triển logic.'),
('V7-47','Theo đó','随之 + V','Sự việc sau thay đổi cùng sự việc trước.','需求下降，价格也随之发生变化。','Nhu cầu giảm, giá cũng theo đó thay đổi.','Phải có yếu tố thay đổi trước.'),
('V7-48','Cho đến, thậm chí','乃至 + N/V','Mở rộng phạm vi theo mức tăng tiến.','这一问题影响个人、家庭乃至整个社会。','Vấn đề này ảnh hưởng cá nhân, gia đình, thậm chí toàn xã hội.','Sắp xếp phạm vi từ nhỏ đến lớn.'),
('V7-49','Đến mức','以至 + kết quả','Nêu kết quả phát triển đến mức cao.','信息过多，以至人们难以判断重点。','Thông tin quá nhiều đến mức người ta khó xác định trọng điểm.','Vế trước phải giải thích được kết quả.'),
('V7-50','Dẫn đến','致使 + kết quả','Nêu nguyên nhân gây kết quả, thường tiêu cực và trang trọng.','管理混乱致使项目进度严重落后。','Quản lý hỗn loạn khiến tiến độ dự án chậm nghiêm trọng.','Chủ ngữ trước 致使 phải là nguyên nhân.'),
('V7-51','Từ đó đạt…','从而 + kết quả','Nêu kết quả logic hoặc mục tiêu đạt được.','建立统一标准，从而降低沟通成本。','Thiết lập tiêu chuẩn thống nhất, từ đó giảm chi phí giao tiếp.','Không dùng chỉ để nối hai sự việc đồng thời.'),
('V7-52','Để tiện','以便 + mục đích','Nêu mục đích tạo thuận lợi cho bước sau.','请保留原始数据，以便日后核查。','Hãy giữ dữ liệu gốc để tiện kiểm tra sau này.','Mục đích chưa phải kết quả thực tế.'),
('V7-53','Để tránh','以免 + hậu quả xấu','Thực hiện hành động nhằm tránh rủi ro.','应明确责任，以免出现相互推诿。','Nên làm rõ trách nhiệm để tránh đùn đẩy lẫn nhau.','Vế sau là hậu quả cần phòng.'),
('V7-54','Để không đến nỗi','不致 + V/Adj','Nêu kết quả tiêu cực được tránh hoặc mức không quá nghiêm trọng.','及时调整可以使损失不致扩大。','Điều chỉnh kịp thời có thể khiến tổn thất không mở rộng.','不致 thường dùng trong văn viết.'),
('V7-55','Phụ thuộc vào, nhờ vào','有赖于 + N/V','Kết quả cần dựa vào một điều kiện hoặc sự hỗ trợ.','制度能否落实有赖于有效监督。','Chế độ có được thực hiện hay không phụ thuộc vào giám sát hiệu quả.','Có thể mang nghĩa điều kiện cần, không chỉ nguyên nhân.'),
('V7-56','Tùy thuộc vào','取决于 + N/V','Kết quả do yếu tố sau quyết định.','方案是否可行取决于实际条件。','Phương án có khả thi hay không tùy thuộc điều kiện thực tế.','Chủ thể kết quả đứng trước 取决于.'),
('V7-57','Nhằm mục đích','旨在 + V','Nêu mục tiêu chính thức của chính sách hoặc hành động.','新措施旨在提高公共服务效率。','Biện pháp mới nhằm nâng hiệu suất dịch vụ công.','旨在 không mô tả kết quả đã đạt.'),
('V7-58','Có ý định','意在 + V','Nêu dụng ý hoặc mục đích, đôi khi mang tính phân tích.','这一调整意在回应市场变化。','Điều chỉnh này nhằm phản hồi thay đổi thị trường.','Có thể hàm ý suy đoán về ý đồ.'),
('V7-59','Liên quan đến','涉及 + N','Nội dung chạm đến một hoặc nhiều lĩnh vực/đối tượng.','该问题涉及法律、技术和管理多个方面。','Vấn đề này liên quan nhiều mặt pháp luật, kỹ thuật và quản lý.','涉及 là động từ, không cần 对 trước tân ngữ.'),
('V7-60','Bao gồm toàn bộ','涵盖 + N','Phạm vi nội dung bao quát các phần.','课程涵盖听、说、读、写等技能。','Khóa học bao quát các kỹ năng nghe, nói, đọc, viết.','Phân biệt 涵盖 phạm vi với 包括 liệt kê trung tính.'),
]
    return [gi(*r) for r in rows]

GRAMMAR = {5:grammar5(),6:grammar6(),7:grammar7()}


def normalize_senses(word):
    primary, senses, measures = base.normalize_senses(word)
    override = PRIMARY_OVERRIDES.get(word['simplified'])
    if override:
        primary = override
        parts = [x.strip() for x in override.split(';') if x.strip()]
        senses = parts + [x for x in senses if x not in parts]
    return primary, senses, measures


def candidate_indexes(prepared):
    by_char, by_py, by_topic, by_pos = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for i,w in enumerate(prepared):
        for c in set(w['simplified']): by_char[c].append(i)
        p = re.sub(r'\d|\s','',w.get('pinyinNumbered','')).lower()
        if p: by_py[p].append(i)
        by_topic[w['_topic']].append(i)
        for pos in w.get('pos') or []: by_pos[pos].append(i)
    return by_char,by_py,by_topic,by_pos


def nearby(rows, center, radius=45):
    if not rows: return []
    at = bisect.bisect_left(rows, center)
    return rows[max(0, at-radius):min(len(rows), at+radius+1)]


def make_pack(level):
    payload=json.loads((ROOT/f'data/levels/hsk{level}.json').read_text(encoding='utf-8'))
    prepared=[]
    for word in payload['words']:
        primary,senses,measures=normalize_senses(word)
        row=dict(word); row['_primary']=primary; row['_senses']=senses; row['_measures']=measures
        row['_topic']=base.topic_for(word,primary,senses)
        prepared.append(row)
    by_char,by_py,by_topic,by_pos=candidate_indexes(prepared)
    q={}
    for i,word in enumerate(prepared):
        candidates=set()
        for c in set(word['simplified']): candidates.update(by_char[c])
        p=re.sub(r'\d|\s','',word.get('pinyinNumbered','')).lower()
        if p: candidates.update(by_py[p])
        candidates.update(nearby(by_topic[word['_topic']], i, 55))
        for pos in word.get('pos') or []: candidates.update(nearby(by_pos[pos], i, 35))
        candidates.update(range(max(0,i-20), min(len(prepared),i+21)))
        candidates.discard(i)
        ranked=sorted((prepared[j] for j in candidates),key=lambda x:(-base.similarity(word,x),x['id']))
        conf=[]
        for cand in ranked:
            if base.similarity(word,cand)<5: break
            if cand['simplified'] not in conf: conf.append(cand['simplified'])
            if len(conf)>=5: break
        curated=CURATED_EXAMPLES.get(level,{}).get(word['simplified'])
        base_ex=word.get('example')
        grammar_ex=None
        for item in GRAMMAR[level]:
            ex=(item.get('examples') or [{}])[0]
            marker=f"{item.get('title','')} {item.get('formula','')}"
            if word['simplified'] in marker and word['simplified'] in ex.get('zh',''):
                grammar_ex=ex; break
        if base_ex:
            example={**base_ex,'kind':'usage','exerciseEligible':True}
        elif curated:
            zh,vi=curated
            example={'zh':zh,'pinyin':py(zh),'vi':vi,'status':'bien_soan_he_thong','kind':'usage','exerciseEligible':True}
        elif grammar_ex:
            example={**grammar_ex,'status':'bien_soan_ngu_phap','kind':'usage','exerciseEligible':True}
        else:
            example={'zh':f'请读这个词：“{word["simplified"]}”。','pinyin':f'Qǐng dú zhège cí: “{word["pinyin"]}”.','vi':f'Hãy đọc từ “{word["simplified"]}”.','status':'mau_doc_tu','kind':'pronunciation','exerciseEligible':False}
        q[word['id']]={
          'wordId':word['id'],'primaryMeaning':word['_primary'],'normalizedSenses':word['_senses'],
          'pos':word.get('pos') or [],'topic':word['_topic'],'measureWords':word['_measures'],
          'usageNote':base.usage_note(word,level,word['_topic'],word['_measures']),
          'collocations':CURATED_COLLOCATIONS.get(word['simplified'],[]),'confusables':conf,'example':example,
          'standardization':{'version':f'HSK{level}-Q1','status':'chuan_hoa_he_thong','reviewedBy':'đối chiếu chữ–pinyin + làm sạch nghĩa + quy tắc ngữ cảnh','updatedAt':TODAY}
        }
    label='7–9' if level==7 else str(level)
    return {'meta':{'level':str(level),'displayLevel':label,'version':'5.0.0','wordCount':len(q),'description':f'Lớp chuẩn hóa HSK {label}: làm sạch nghĩa, từ loại, chủ đề, ghi chú cách dùng, từ dễ nhầm và ví dụ an toàn.'},'words':q}


def main():
    for level in LEVELS:
        pack=make_pack(level)
        (ROOT/f'data/hsk{level}-quality.json').write_text(json.dumps(pack,ensure_ascii=False,indent=2),encoding='utf-8')
        label='7–9' if level==7 else str(level)
        grammar={'meta':{'level':str(level),'displayLevel':label,'version':'5.0.0','itemCount':len(GRAMMAR[level]),'description':f'Các cấu trúc ngữ pháp trọng tâm HSK {label}, có công thức, giải thích, ví dụ và lỗi thường gặp.'},'items':GRAMMAR[level]}
        (ROOT/f'data/hsk{level}-grammar.json').write_text(json.dumps(grammar,ensure_ascii=False,indent=2),encoding='utf-8')
        eligible=sum(1 for x in pack['words'].values() if x['example']['exerciseEligible'])
        print(f'HSK {label}: {len(pack["words"])} từ, {len(GRAMMAR[level])} điểm ngữ pháp, {eligible} ví dụ luyện tập')

if __name__=='__main__': main()
