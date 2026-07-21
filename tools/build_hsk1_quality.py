#!/usr/bin/env python3
import json,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=json.loads((ROOT/'data/levels/hsk1.json').read_text(encoding='utf-8'))
words=source['words']

TOPICS={
'gia đình & con người': {'爸爸','妈妈','哥哥','姐姐','弟弟','妹妹','爷爷','奶奶','外公','外婆','儿子','女儿','孩子','男孩儿','女孩儿','小孩儿','人','男人','女人','朋友','同学','老师','学生','医生','先生','小姐','大家','自己'},
'số đếm & số lượng': {'零','一','二','两','三','四','五','六','七','八','九','十','百','千','万','第一','第二','半','多少','几','一些','一点儿','个','本','杯','件','口','块','岁','位','只','张','次'},
'thời gian & lịch': {'今天','昨天','明天','现在','时候','时间','年','月','日','号','星期','周','早上','上午','中午','下午','晚上','白天','每天','今年','去年','明年','点','分钟','小时','一会儿','半天'},
'địa điểm & phương hướng': {'中国','北京','家','学校','医院','商店','饭店','机场','火车站','车站','公司','房间','里','外','上','下','前','后','左','右','东','西','南','北','这儿','那儿','哪儿','地方','路'},
'ăn uống': {'米饭','面条儿','包子','饺子','菜','水果','苹果','西瓜','茶','咖啡','水','牛奶','鸡蛋','肉','鱼','饭','早饭','午饭','晚饭','吃','喝','好吃','饿','渴'},
'học tập & ngôn ngữ': {'学习','学生','老师','学校','书','本子','笔','字','汉字','中文','汉语','英语','课','考试','问题','题','读','写','说','听','看','认识','知道','明白','回答','问','教','词语','名字'},
'công việc & sinh hoạt': {'工作','上班','下班','休息','起床','睡觉','洗澡','穿','买','卖','开','关','打开','帮助','准备','开始','完','做','找','等','给','拿','放','用'},
'giao thông & đi lại': {'车','出租车','公共汽车','地铁','火车','飞机','自行车','开车','坐','骑','走','跑','来','去','回','到','进','出','上车','下车','打车','路'},
'đồ vật & nhà cửa': {'桌子','椅子','床','门','窗户','电视','电脑','手机','电话','衣服','鞋','帽子','杯子','盘子','筷子','包','钱','票','门票','照片','东西','房子'},
'thời tiết & tự nhiên': {'天气','下雨','下雪','风','太阳','晴','阴','冷','热','凉快','春天','夏天','秋天','冬天','山','水','花','树','猫','狗','鸟'},
'cơ thể & sức khỏe': {'身体','头','脸','眼睛','耳朵','嘴','手','脚','肚子','病','生病','药','健康','累','疼','高','矮','胖','瘦'},
'cảm xúc & đánh giá': {'爱','喜欢','高兴','快乐','生气','害怕','觉得','希望','想','好','坏','漂亮','可爱','有意思','好玩儿','对','错','难','容易','重要'},
'mua sắm & tiền': {'买','卖','钱','块','元','贵','便宜','商店','东西','多少','要','给','找钱'},
'giao tiếp & xã hội': {'你好','谢谢','不客气','对不起','没关系','再见','请','喂','欢迎','祝','生日','名字','姓','叫','介绍','认识','告诉','说话','聊天','一起'},
}

SPECIAL_NOTES={
'爱':'Dùng cho tình cảm hoặc sở thích mạnh; với hoạt động thường ngày có thể dùng 喜欢 tự nhiên hơn.',
'爱好':'Có thể là danh từ “sở thích” hoặc động từ “yêu thích”.',
'会':'Có thể chỉ năng lực đã học được, khả năng xảy ra hoặc tương lai tùy ngữ cảnh.',
'能':'Nhấn mạnh điều kiện/khả năng thực tế; khác 会 là kỹ năng đã học.',
'可以':'Dùng để xin phép, cho phép hoặc nói điều kiện cho phép.',
'想':'Có thể là “muốn”, “nghĩ” hoặc “nhớ”; cần dựa vào tân ngữ/ngữ cảnh.',
'要':'Có thể là “muốn/cần”, “sắp”, hoặc yêu cầu; sắc thái mạnh hơn 想.',
'有':'Phủ định là 没有, không dùng 不有.',
'是':'Phủ định thông thường là 不是.',
'在':'Có thể là động từ “ở” hoặc giới từ đánh dấu nơi diễn ra hành động.',
'了':'Trợ từ chỉ sự thay đổi hoặc hành động hoàn thành; vị trí quyết định sắc thái.',
'的':'Đứng giữa định ngữ và danh từ; đôi khi lược danh từ khi ngữ cảnh đã rõ.',
'吗':'Đặt cuối câu để tạo câu hỏi có/không.',
'呢':'Dùng hỏi lại, hỏi tình trạng hoặc làm câu hỏi mềm hơn.',
'吧':'Dùng gợi ý, đề nghị hoặc phỏng đoán nhẹ.',
'二':'Dùng trong số đếm, số thứ tự và số điện thoại; trước lượng từ thường dùng 两.',
'两':'Dùng trước lượng từ hoặc danh từ đơn vị; không dùng cho số thứ tự.',
'一点儿':'Chỉ một lượng nhỏ; thường đứng sau tính từ hoặc trước danh từ tùy cấu trúc.',
'一下儿':'Đặt sau động từ để làm hành động ngắn, thử hoặc làm nhẹ sắc thái yêu cầu.',
'怎么':'Hỏi cách thức hoặc nguyên nhân tùy ngữ điệu/ngữ cảnh.',
'怎么样':'Hỏi đánh giá, tình trạng hoặc đề nghị ý kiến.',
'几':'Hỏi số lượng nhỏ, thường dưới mười và thường đi với lượng từ.',
'多少':'Hỏi số lượng không giới hạn và có thể hỏi giá tiền.',
}

COLLOC={
'爱':['爱家人','爱学习','爱运动'],'喜欢':['喜欢吃','喜欢看书','很喜欢'],'学习':['学习中文','努力学习','一起学习'],'工作':['找工作','上班工作','工作很忙'],
'吃':['吃饭','吃水果','吃早饭'],'喝':['喝水','喝茶','喝咖啡'],'看':['看书','看电视','看医生'],'听':['听音乐','听老师说','听得懂'],
'说':['说中文','慢慢说','说一遍'],'写':['写汉字','写名字','写作业'],'读':['读书','读课文','大声读'],'买':['买东西','买衣服','花钱买'],
'去':['去学校','去上班','一起去'],'来':['来中国','来我家','明天来'],'回':['回家','回学校','回公司'],'坐':['坐车','坐地铁','请坐'],
'有':['有时间','有问题','家里有'],'没有':['没有时间','还没有','没有问题'],'知道':['我知道','不知道','知道名字'],'认识':['认识朋友','很高兴认识你','不认识'],
'觉得':['觉得很好','我觉得','觉得累'],'想':['想去','想吃','我想你'],'要':['要一杯茶','不要','快要'],'可以':['可以进来','可以吗','不可以'],
'会':['会说中文','会开车','不会'],'能':['能听懂','能不能','不能'],'帮':['帮我','帮助别人','帮忙'],'给':['给我','送给','给你打电话'],
'好':['很好','好朋友','好吃'],'大':['很大','大房子','大一点儿'],'小':['很小','小孩子','小一点儿'],'多':['很多','多大','多一点儿'],'少':['很少','少一点儿','不少'],
}

BAD_SENSE=re.compile(r'^(LT:|Lượng từ:|biến thể|xem\s|cũng viết|cũng đọc)',re.I)
def clean_text(s):
    s=re.sub(r'LT:[^;，。]*','',s)
    s=re.sub(r'\(lượng từ:[^)]*\)','',s,flags=re.I)
    s=re.sub(r'\s+',' ',s).strip(' ;，,')
    return s

def topic_for(word):
    s=word['simplified']
    for topic,items in TOPICS.items():
        if s in items:return topic
    poses=set(word.get('pos') or [])
    if 'đại từ' in poses:return 'đại từ & chỉ định'
    if 'số từ' in poses or 'lượng từ' in poses:return 'số đếm & số lượng'
    if 'trợ từ' in poses or 'giới từ' in poses or 'liên từ' in poses:return 'từ chức năng & ngữ pháp'
    if 'động từ' in poses:return 'động từ thông dụng'
    if 'tính từ' in poses:return 'miêu tả & đánh giá'
    return 'từ vựng cơ bản'

def generic_note(word,measure):
    s=word['simplified']; poses='; '.join(word.get('pos') or []) or 'từ'
    if s in SPECIAL_NOTES:return SPECIAL_NOTES[s]
    if measure:return f'{s} chủ yếu dùng như {poses}. Lượng từ thường gặp: {", ".join(measure)}.'
    if 'lượng từ' in (word.get('pos') or []):return f'{s} là lượng từ; cần chú ý loại danh từ có thể đi kèm.'
    if 'trợ từ' in (word.get('pos') or []):return f'{s} là trợ từ; ý nghĩa phụ thuộc vị trí và cấu trúc câu.'
    if 'động từ' in (word.get('pos') or []):return f'{s} là động từ HSK 1 thông dụng; nên học cùng tân ngữ/cụm từ thường đi kèm.'
    if 'tính từ' in (word.get('pos') or []):return f'{s} là tính từ; trong câu miêu tả thường có phó từ mức độ như 很.'
    return f'{s} là {poses} thuộc HSK 1; ưu tiên nghĩa thông dụng trong giao tiếp cơ bản.'

def normalize_senses(word):
    kept=[]; measure=[]
    for sense in word.get('senses',[]):
        text=clean_text(sense.get('vi',''))
        raw=sense.get('vi','')
        if raw.startswith(('LT:','Lượng từ:')):
            parts=re.findall(r'[\u4e00-\u9fff]+',raw)
            measure.extend(parts[:4]); continue
        if not text or BAD_SENSE.match(text):continue
        text=re.sub(r'^\((thông tục|văn học|khẩu ngữ)\)\s*','',text,flags=re.I)
        if text not in kept:kept.append(text)
    if not kept:kept=[clean_text(word.get('meaning','')) or 'Cần bổ sung nghĩa']
    primary=kept[0]
    # Giới hạn nghĩa chính để giao diện rõ hơn, vẫn giữ toàn bộ nghĩa phụ trong normalizedSenses.
    primary='; '.join([x.strip() for x in primary.split(';')[:3] if x.strip()])
    return primary,kept[:8],list(dict.fromkeys(measure))

def similarity(a,b):
    score=0
    if a.get('pinyinNumbered')==b.get('pinyinNumbered'):score+=10
    pa=re.sub(r'\d|\s','',a.get('pinyinNumbered','')); pb=re.sub(r'\d|\s','',b.get('pinyinNumbered',''))
    if pa==pb:score+=7
    sa=a['simplified']; sb=b['simplified']
    common=len(set(sa)&set(sb)); score+=common*3
    if set(a.get('pos',[]))&set(b.get('pos',[])):score+=2
    ma=set(re.findall(r'[A-Za-zÀ-ỹ]+',a.get('_primary','').lower())); mb=set(re.findall(r'[A-Za-zÀ-ỹ]+',b.get('_primary','').lower()))
    score+=min(3,len(ma&mb))
    return score

prepared=[]
for w in words:
    primary,senses,measure=normalize_senses(w)
    x=dict(w); x['_primary']=primary; x['_norm_senses']=senses; x['_measure']=measure; prepared.append(x)

quality={}
for w in prepared:
    ranked=sorted((x for x in prepared if x['id']!=w['id']),key=lambda x:(-similarity(w,x),x['id']))
    conf=[]
    for x in ranked:
        if similarity(w,x)<3:break
        if x['simplified'] not in conf:conf.append(x['simplified'])
        if len(conf)>=4:break
    example=w.get('example')
    if example:
        learning_example={**example,'kind':'usage','exerciseEligible':True}
    else:
        learning_example={
          'zh':f'我会说“{w["simplified"]}”。',
          'pinyin':f'Wǒ huì shuō “{w["pinyin"]}”.',
          'vi':f'Tôi có thể đọc từ “{w["simplified"]}”.',
          'status':'mau_doc_tu','kind':'pronunciation','exerciseEligible':False
        }
    quality[w['id']]={
      'wordId':w['id'],'primaryMeaning':w['_primary'],'normalizedSenses':w['_norm_senses'],
      'pos':w.get('pos') or [],'topic':topic_for(w),'measureWords':w['_measure'],
      'usageNote':generic_note(w,w['_measure']),'collocations':COLLOC.get(w['simplified'],[]),
      'confusables':conf,'example':learning_example,
      'standardization':{'version':'HSK1-Q1','status':'chuan_hoa_ban_dau','reviewedBy':'hệ thống + dữ liệu đối chiếu','updatedAt':'2026-07-21'}
    }

out={'meta':{'level':'1','version':'3.0.0','wordCount':len(quality),'description':'Lớp chuẩn hóa HSK 1: nghĩa chính gọn, từ loại, chủ đề, lượng từ, ghi chú, cụm từ, từ dễ nhầm và ví dụ.'},'words':quality}
(ROOT/'data/hsk1-quality.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Wrote',len(quality),'quality records')
