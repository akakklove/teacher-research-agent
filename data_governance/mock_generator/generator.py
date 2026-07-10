"""
Mock 数据生成器 — 生成有业务特征的模拟科研数据
保证 18 张表之间的外键一致性和业务合理性
"""
import random
import string
from datetime import date, timedelta, datetime
from dataclasses import dataclass, field
from typing import Optional
import pymysql


# ============================================
# 业务特征配置 — 让数据看起来像真的
# ============================================

SEED = 42  # 固定种子，保证每次运行生成相同数据
random.seed(SEED)

CONFIG = {
    "teacher_count": 50,
    "project_count": 200,
    "paper_count": 300,
    "patent_count": 80,
    "book_count": 40,
    "software_count": 50,
    "award_count": 60,
    "conference_count": 30,
    "institution_count": 15,
    "date_start": date(2022, 1, 1),
    "date_end": date(2025, 12, 31),
}

# 院系 — 不同学院有不同的科研特征
DEPARTMENTS = [
    {"code": "CS",  "name": "计算机学院",     "project_factor": 2.0, "paper_factor": 2.5, "fund_factor": 3.0},
    {"code": "EE",  "name": "电子工程学院",   "project_factor": 1.5, "paper_factor": 1.5, "fund_factor": 1.8},
    {"code": "ME",  "name": "机械工程学院",   "project_factor": 1.2, "paper_factor": 1.0, "fund_factor": 1.5},
    {"code": "CIVIL","name": "土木工程学院",  "project_factor": 1.0, "paper_factor": 0.8, "fund_factor": 1.2},
    {"code": "CHEM", "name": "化学学院",       "project_factor": 1.3, "paper_factor": 1.8, "fund_factor": 1.3},
    {"code": "BIO",  "name": "生命科学学院",  "project_factor": 1.4, "paper_factor": 2.0, "fund_factor": 1.6},
    {"code": "MATH", "name": "数学学院",       "project_factor": 0.6, "paper_factor": 1.2, "fund_factor": 0.5},
    {"code": "PHY",  "name": "物理学院",       "project_factor": 1.0, "paper_factor": 1.5, "fund_factor": 1.0},
    {"code": "ECON", "name": "经济管理学院",   "project_factor": 0.5, "paper_factor": 0.5, "fund_factor": 0.4},
    {"code": "LAW",  "name": "法学院",         "project_factor": 0.3, "paper_factor": 0.3, "fund_factor": 0.2},
]

# 姓氏 + 名字（常见组合）
SURNAMES = ["张","王","李","赵","陈","刘","杨","黄","周","吴","徐","孙","马","朱","胡","郭","何","高","林","罗","郑","梁","谢","宋","唐","韩","曹","许","邓","冯","萧","程","曾","彭","吕","苏","卢","蒋","蔡","贾","魏","薛","叶","阎","余","潘","杜","戴","夏","钟","汪","田","任","姜","范","方","石","姚","谭","廖","邹","熊","金","陆","郝","孔","白","崔","康","毛","邱","秦","江","史","顾","侯","邵","孟","龙","万","段","雷","钱","汤","尹","易","常","武","乔","贺","赖","龚","文"]
GIVEN_NAMES_MALE = ["建国","伟","强","磊","军","勇","涛","斌","鹏","明","华","峰","宇","辉","浩","志","文","刚","杰","飞","毅","超","亮","健","波","宁","旭","博","鑫","睿","晨","哲","浩宇","子涵","浩然","天佑","子轩","奕辰","泽洋","铭泽"]
GIVEN_NAMES_FEMALE = ["芳","敏","静","丽","秀英","艳","娜","婷","雪","琳","萍","琴","慧","洁","云","霞","莉","娟","红","玲","梅","燕","桂英","淑珍","秀兰","秀芳","慧敏","文静","雨涵","梓涵","诗涵","梦瑶","欣怡","子萱","晓婷","思雨"]

# 职称
TITLES = ["教授","副教授","讲师","助教"]
TITLE_WEIGHTS = [0.25, 0.35, 0.30, 0.10]  # 教授25%，副教授35%，讲师30%，助教10%

# 项目级别
PROJECT_LEVELS = ["GJJZD","GJJYB","SBJZD","SBJYB","TJYB","QYWT"]
LEVEL_NAMES = {"GJJZD":"国家级重点","GJJYB":"国家级一般","SBJZD":"省部级重点","SBJYB":"省部级一般","TJYB":"厅局级","QYWT":"企业委托"}

# 项目来源
PROJECT_SOURCES = ["NSFC","MOST","MOE","PROV","ENTERPRISE","OTHER"]
SOURCE_NAMES = {"NSFC":"国家自然科学基金委","MOST":"科技部","MOE":"教育部","PROV":"省科技厅","ENTERPRISE":"企业委托","OTHER":"其他"}

# 期刊级别
JOURNAL_LEVELS = ["SCI-1","SCI-2","SCI-3","EI","CORE","OTHER"]

# 获奖级别
AWARD_LEVELS = ["GJJ","SBJ","TJ","XJ"]
AWARD_NAMES = {"GJJ":"国家级","SBJ":"省部级","TJ":"厅局级","XJ":"校级"}

# 经费科目
FUND_CATEGORIES = ["设备费","材料费","测试化验加工费","差旅费","会议费","国际合作与交流费","出版/文献/信息传播费","劳务费","专家咨询费","其他支出","管理费","绩效支出"]

# 出版社
PUBLISHERS = ["科学出版社","高等教育出版社","清华大学出版社","电子工业出版社","机械工业出版社","人民邮电出版社","北京大学出版社","浙江大学出版社","化学工业出版社","中国科学技术出版社"]

# 专利类型
PATENT_TYPES = {"FM":"发明专利","SY":"实用新型","WG":"外观设计"}

TOTAL_TEACHERS = CONFIG["teacher_count"]
TOTAL_PROJECTS = CONFIG["project_count"]


def random_date(start=None, end=None):
    """生成随机日期"""
    s = start or CONFIG["date_start"]
    e = end or CONFIG["date_end"]
    days = (e - s).days
    return s + timedelta(days=random.randint(0, days))


def random_name():
    """生成随机中文姓名"""
    surname = random.choice(SURNAMES)
    if random.random() > 0.5:
        given = random.choice(GIVEN_NAMES_MALE)
    else:
        given = random.choice(GIVEN_NAMES_FEMALE)
    return surname + given


def generate_teacher_id(i):
    """生成工号：GH + 年份 + 4位序号"""
    return f"GH{2020 + (i // 20):04d}{i:04d}"


def generate_project_id(i):
    """生成项目编号：KY + 年份 + 4位序号"""
    return f"KY{2022 + (i // 50):04d}{i:04d}"


def generate_paper_id(i):
    return f"LW{2022 + (i // 80):04d}{i:04d}"


def generate_patent_id(i):
    return f"ZL{2022 + (i // 30):04d}{i:04d}"


def generate_book_id(i):
    return f"ZZ{2022 + (i // 15):04d}{i:04d}"


def generate_software_id(i):
    return f"RJ{2022 + (i // 20):04d}{i:04d}"


def generate_award_id(i):
    return f"HJ{2022 + (i // 20):04d}{i:04d}"


def generate_conference_id(i):
    return f"HY{2022 + (i // 10):04d}{i:04d}"


def generate_institution_id(i):
    return f"JG{2020 + i:04d}"


# ============================================
# 主生成器
# ============================================
@dataclass
class MockData:
    """存储所有生成的 Mock 数据"""
    teachers: list = field(default_factory=list)
    projects: list = field(default_factory=list)
    project_members: list = field(default_factory=list)
    fund_arrivals: list = field(default_factory=list)
    fund_expenses: list = field(default_factory=list)
    fund_transfers: list = field(default_factory=list)
    papers: list = field(default_factory=list)
    paper_authors: list = field(default_factory=list)
    patents: list = field(default_factory=list)
    patent_inventors: list = field(default_factory=list)
    books: list = field(default_factory=list)
    book_authors: list = field(default_factory=list)
    software: list = field(default_factory=list)
    software_members: list = field(default_factory=list)
    awards: list = field(default_factory=list)
    award_members: list = field(default_factory=list)
    conferences: list = field(default_factory=list)
    institutions: list = field(default_factory=list)
    institution_members: list = field(default_factory=list)


def generate_all() -> MockData:
    """生成全部 Mock 数据"""
    data = MockData()
    
    # Step 1: 生成教师
    print("生成教师...")
    data.teachers = _generate_teachers()
    
    # Step 2: 生成项目 + 项目人员
    print("生成科研项目...")
    _generate_projects(data)
    
    # Step 3: 生成经费
    print("生成经费数据...")
    _generate_funding(data)
    
    # Step 4: 生成成果
    print("生成论文...")
    _generate_papers(data)
    print("生成专利...")
    _generate_patents(data)
    print("生成著作...")
    _generate_books(data)
    print("生成软著...")
    _generate_software(data)
    print("生成获奖...")
    _generate_awards(data)
    
    # Step 5: 生成学术活动
    print("生成学术会议...")
    _generate_conferences(data)
    print("生成科研机构...")
    _generate_institutions(data)
    
    print(f"\n✅ Mock 数据生成完成!")
    _print_summary(data)
    return data


def _generate_teachers():
    """生成 50 个教师"""
    teachers = []
    for i in range(TOTAL_TEACHERS):
        dept = DEPARTMENTS[i % len(DEPARTMENTS)]
        title = random.choices(TITLES, weights=TITLE_WEIGHTS, k=1)[0]
        gh = generate_teacher_id(i + 1)
        name = random_name()
        # 确保名字不重复
        while any(t["xm"] == name for t in teachers):
            name = random_name()
        
        teachers.append({
            "id": i + 1,
            "gh": gh,
            "xm": name,
            "xb": random.choice(["男","女"]),
            "dw_bm": dept["code"],
            "dw_mc": dept["name"],
            "zc": title,
            "xkml_bm": f"{random.randint(7,12):02d}",
            "ryrq": str(random_date(date(2010,1,1), date(2022,12,31))),
        })
    return teachers


def _generate_projects(data: MockData):
    """生成 200 个项目 + 项目人员关系"""
    for i in range(TOTAL_PROJECTS):
        # 随机选一个教师作为项目负责人
        leader = random.choice(data.teachers)
        dept = next(d for d in DEPARTMENTS if d["code"] == leader["dw_bm"])
        
        # 项目级别 — 教授更容易拿到高级别项目
        if leader["zc"] == "教授":
            level_w = [0.15, 0.25, 0.20, 0.20, 0.10, 0.10]
        elif leader["zc"] == "副教授":
            level_w = [0.05, 0.15, 0.20, 0.30, 0.15, 0.15]
        else:
            level_w = [0.01, 0.05, 0.10, 0.20, 0.25, 0.39]
        level = random.choices(PROJECT_LEVELS, weights=level_w, k=1)[0]
        
        # 经费 — 高级别项目经费多
        fund_base = {"GJJZD": (500000, 5000000), "GJJYB": (200000, 1500000),
                     "SBJZD": (100000, 800000), "SBJYB": (50000, 500000),
                     "TJYB": (10000, 200000), "QYWT": (50000, 2000000)}
        lo, hi = fund_base[level]
        ht_jf = round(random.uniform(lo, hi) * dept["fund_factor"], 2)
        pt_jf = round(ht_jf * random.uniform(0, 0.3), 2)  # 配套经费 0~30%
        
        lxrq = random_date()
        ksrq = lxrq + timedelta(days=random.randint(0, 30))
        jhwcrq = ksrq + timedelta(days=random.randint(365, 1095))
        
        # 执行状态 — 大部分在研，少部分已结题
        if lxrq < date(2024, 1, 1):
            status = random.choices(["JIETI","ZAIYAN"], weights=[0.7, 0.3], k=1)[0]
        else:
            status = random.choices(["ZAIYAN","JIETI","ZHONGZHI"], weights=[0.8, 0.1, 0.1], k=1)[0]
        
        if status == "JIETI" and lxrq < date(2024, 7, 1):
            jxrq = str(random_date(lxrq + timedelta(days=365), date(2025, 12, 31)))
        elif status == "JIETI":
            jxrq = str(lxrq + timedelta(days=random.randint(180, 365)))
        else:
            jxrq = None
        
        kybh = generate_project_id(i + 1)
        project = {
            "id": i + 1,
            "kybh": kybh,
            "xmmc": _gen_project_name(level, dept["name"]),
            "xmbh_xn": f"XN{kybh[2:]}",
            "ssdw_bm": dept["code"],
            "xmlx_bm": random.choice(PROJECT_SOURCES),
            "xmxz_bm": random.choice(["ZX","HX"]),
            "xmjb_bm": level,
            "xkml_bm": f"{random.randint(7,12):02d}",
            "lxrq": str(lxrq),
            "ksrq": str(ksrq),
            "jxrq": jxrq,
            "jhwcrq": str(jhwcrq),
            "fzr_gh": leader["gh"],
            "ht_jf": ht_jf,
            "pt_jf": pt_jf,
            "zxzt_bm": status,
            "htbh": f"HT-{kybh}",
            "jfkh": f"JF-{kybh[2:]}",
        }
        data.projects.append(project)
        
        # 项目人员：负责人 + 0~4 个参与人
        members = [{
            "kybh": kybh,
            "ry_gh": leader["gh"],
            "ry_xm": leader["xm"],
            "dw_bm": leader["dw_bm"],
            "rylx_bm": "BXJS",
            "ryjs_bm": "FZR",
            "smsx": 1,
            "gxl": round(random.uniform(30, 60), 2),
        }]
        
        # 添加参与人
        n_participants = random.choices([0,1,2,3,4], weights=[0.2,0.3,0.3,0.15,0.05], k=1)[0]
        other_teachers = [t for t in data.teachers if t["gh"] != leader["gh"] and t["dw_bm"] == leader["dw_bm"]]
        if not other_teachers:
            other_teachers = [t for t in data.teachers if t["gh"] != leader["gh"]]
        
        selected = random.sample(other_teachers, min(n_participants, len(other_teachers)))
        remaining_gxl = 100 - members[0]["gxl"]
        for j, t in enumerate(selected):
            if j == len(selected) - 1:
                gxl = round(remaining_gxl, 2)
            else:
                gxl = round(random.uniform(5, remaining_gxl * 0.6), 2)
                remaining_gxl -= gxl
            members.append({
                "kybh": kybh,
                "ry_gh": t["gh"],
                "ry_xm": t["xm"],
                "dw_bm": t["dw_bm"],
                "rylx_bm": "BXJS",
                "ryjs_bm": "CYR",
                "smsx": j + 2,
                "gxl": gxl,
            })
        
        data.project_members.extend(members)


def _gen_project_name(level, dept_name):
    """生成有意义的项目名称"""
    nouns = ["智能","大数据","多模态","深度学习","高性能","自适应","分布式","轻量化","可信","绿色"]
    topics = ["关键技术研究","模型构建与应用","算法优化","系统研发","平台建设","评估方法研究","融合方法研究"]
    return f"面向{dept_name}的{random.choice(nouns)}{random.choice(topics)}"


def _generate_funding(data: MockData):
    """为每个在研/已结题项目生成经费到账和支出"""
    today = date.today()
    for proj in data.projects:
        kybh = proj["kybh"]
        
        # 查一下项目负责人
        members = [m for m in data.project_members if m["kybh"] == kybh]
        if not members:
            continue
        
        lxrq = date.fromisoformat(proj["lxrq"])
        end_date = date.fromisoformat(proj["jxrq"]) if proj.get("jxrq") else today
        
        # 经费到账 — 分批次
        total_fund = float(proj["ht_jf"]) + float(proj["pt_jf"])
        n_batches = random.randint(1, min(5, (end_date.year - lxrq.year) * 2 + 1))
        remaining = total_fund
        for b in range(n_batches):
            pz_date = random_date(lxrq, end_date)
            if b == n_batches - 1:
                dz_je = round(remaining, 2)
            else:
                dz_je = round(random.uniform(remaining * 0.1, remaining * 0.5), 2)
                remaining -= dz_je
            data.fund_arrivals.append({
                "cw_xmbh": f"CW-{kybh[2:]}",
                "kybh": kybh,
                "km_bh": f"KM{random.randint(1000,9999)}",
                "km_mc": random.choice(FUND_CATEGORIES),
                "kj_nd": str(pz_date.year),
                "pz_rq": str(pz_date),
                "dz_je": dz_je,
            })
        
        # 经费支出
        total_arrived = sum(f["dz_je"] for f in data.fund_arrivals if f["kybh"] == kybh)
        if total_arrived > 0 and proj["zxzt_bm"] != "ZHONGZHI":
            n_expenses = random.randint(3, 15)
            spent_total = total_arrived * random.uniform(0.3, 0.95)
            remaining_spend = spent_total
            for e in range(n_expenses):
                pz_date = random_date(lxrq, end_date)
                if e == n_expenses - 1:
                    zc_je = round(remaining_spend, 2)
                else:
                    zc_je = round(random.uniform(remaining_spend * 0.05, remaining_spend * 0.3), 2)
                    remaining_spend -= zc_je
                data.fund_expenses.append({
                    "cw_xmbh": f"CW-{kybh[2:]}",
                    "kybh": kybh,
                    "km_bh": f"KM{random.randint(1000,9999)}",
                    "km_mc": random.choice(FUND_CATEGORIES),
                    "kj_nd": str(pz_date.year),
                    "pz_rq": str(pz_date),
                    "zc_je": zc_je,
                })
        
        # 经费外拨 — 部分项目有
        if random.random() < 0.3:
            wb_je = round(total_arrived * random.uniform(0.05, 0.2), 2)
            pz_date = random_date(lxrq, end_date)
            data.fund_transfers.append({
                "cw_xmbh": f"CW-{kybh[2:]}",
                "kybh": kybh,
                "km_bh": f"KM{random.randint(1000,9999)}",
                "km_mc": "外拨经费",
                "kj_nd": str(pz_date.year),
                "pz_rq": str(pz_date),
                "wb_je": wb_je,
            })


def _generate_papers(data: MockData):
    """生成 300 篇论文"""
    for i in range(CONFIG["paper_count"]):
        author = random.choice(data.teachers)
        dept = next(d for d in DEPARTMENTS if d["code"] == author["dw_bm"])
        year = random.randint(2022, 2025)
        
        # 高职称 + 计算机/生物老师更容易发高级别论文
        if author["zc"] in ["教授","副教授"] and dept["code"] in ["CS","BIO","CHEM","PHY","EE"]:
            level_w = [0.10, 0.20, 0.25, 0.15, 0.15, 0.15]
        else:
            level_w = [0.02, 0.08, 0.10, 0.15, 0.30, 0.35]
        kw_jb = random.choices(JOURNAL_LEVELS, weights=level_w, k=1)[0]
        
        lwbh = generate_paper_id(i + 1)
        paper = {
            "id": i + 1,
            "lwbh": lwbh,
            "lwmc": f"基于{random.choice(['深度学习','强化学习','图神经网络','Transformer','知识图谱'])}的{random.choice(['目标检测','语义分割','推荐系统','异常诊断','预测模型'])}研究",
            "lwywmc": f"Research on {random.choice(['Deep Learning','Reinforcement Learning','Graph Neural Networks'])} for {random.choice(['Object Detection','Semantic Segmentation'])}",
            "kwmc": random.choice(["IEEE Trans. on Pattern Analysis","Nature Communications","Science Advances","中国科学","计算机学报","软件学报","自动化学报"]),
            "kwjb": kw_jb,
            "slqk": random.choice(["SCI","EI","ISTP",""]) if kw_jb != "OTHER" else "",
            "fbn": str(year),
            "fbq": str(random.randint(1, 12)),
            "xkml_bm": f"{random.randint(7,12):02d}",
        }
        
        # 关联项目（概率性）
        author_projects = [m for m in data.project_members if m["ry_gh"] == author["gh"]]
        if author_projects and random.random() < 0.6:
            paper["kybh"] = random.choice(author_projects)["kybh"]
        else:
            paper["kybh"] = None
        
        data.papers.append(paper)
        
        # 论文作者 — 第一作者 + 0~2 个通讯作者
        data.paper_authors.append({
            "lwbh": lwbh, "zzgh": author["gh"], "zzxm": author["xm"],
            "dwbm": author["dw_bm"], "smsx": 1, "gxl": round(random.uniform(50, 80), 2)
        })
        
        n_coauthors = random.choices([0,1,2], weights=[0.5,0.3,0.2], k=1)[0]
        coauthors = [t for t in data.teachers if t["gh"] != author["gh"] and t["dw_bm"] == author["dw_bm"]]
        if len(coauthors) > 0:
            selected = random.sample(coauthors, min(n_coauthors, len(coauthors)))
            for j, t in enumerate(selected):
                data.paper_authors.append({
                    "lwbh": lwbh, "zzgh": t["gh"], "zzxm": t["xm"],
                    "dwbm": t["dw_bm"], "smsx": j + 2,
                    "gxl": round(random.uniform(10, 30), 2)
                })


def _generate_patents(data: MockData):
    """生成 80 个专利"""
    for i in range(CONFIG["patent_count"]):
        inventor = random.choice(data.teachers)
        sq_date = random_date()
        zlbh = generate_patent_id(i + 1)
        
        patent = {
            "id": i + 1, "zlbh": zlbh,
            "zlmc": f"一种基于{random.choice(['深度学习','物联网','区块链','边缘计算','计算机视觉'])}的{random.choice(['智能监测','数据加密','目标识别','自适应控制','故障诊断'])}方法及装置",
            "zllx": random.choices(["FM","SY","WG"], weights=[0.4,0.5,0.1], k=1)[0],
            "zlzt": random.choices(["YX","SQ"], weights=[0.7,0.3], k=1)[0],
            "sqrq": str(sq_date),
            "sqrq2": str(sq_date + timedelta(days=random.randint(180, 540))) if random.random() > 0.3 else None,
        }
        
        inventor_projects = [m for m in data.project_members if m["ry_gh"] == inventor["gh"]]
        if inventor_projects and random.random() < 0.5:
            patent["kybh"] = random.choice(inventor_projects)["kybh"]
        else:
            patent["kybh"] = None
        
        data.patents.append(patent)
        
        # 发明人
        data.patent_inventors.append({
            "zlbh": zlbh, "fmr_gh": inventor["gh"], "fmr_xm": inventor["xm"],
            "smsx": 1
        })
        # 加 0~4 个共同发明人
        coinventors = [t for t in data.teachers if t["gh"] != inventor["gh"]]
        n = random.choices([0,1,2,3,4], weights=[0.3,0.3,0.2,0.15,0.05], k=1)[0]
        selected = random.sample(coinventors, min(n, len(coinventors)))
        for j, t in enumerate(selected):
            data.patent_inventors.append({
                "zlbh": zlbh, "fmr_gh": t["gh"], "fmr_xm": t["xm"],
                "smsx": j + 2
            })


def _generate_books(data: MockData):
    """生成 40 本著作"""
    for i in range(CONFIG["book_count"]):
        author = random.choice(data.teachers)
        cb_date = random_date()
        zzbh = generate_book_id(i + 1)
        
        book = {
            "id": i + 1, "zzbh": zzbh,
            "zzmc": f"{random.choice(['深度学习','大数据分析','人工智能','物联网','云计算','智能制造','数字孪生'])}{random.choice(['原理与实践','技术与应用','从入门到精通','核心算法','系统设计与实现'])}",
            "cbs": random.choice(PUBLISHERS),
            "cbrq": str(cb_date),
            "isbn": f"978-7-{random.randint(100,999)}-{random.randint(10000,99999)}-{random.randint(0,9)}",
            "lzlbm": random.choice(["ZZ","JC","YZ"]),
            "yzm": "CN",
            "sfsmbx": "是",
            "zzzs": random.randint(100, 800),
        }
        
        author_projects = [m for m in data.project_members if m["ry_gh"] == author["gh"]]
        book["kybh"] = random.choice(author_projects)["kybh"] if author_projects and random.random() < 0.3 else None
        
        data.books.append(book)
        data.book_authors.append({
            "zzbh": zzbh, "zzryh": author["gh"], "zzxm": author["xm"],
            "cdjs": random.choice(["ZB","FZB"]), "smsx": 1,
            "gxl": round(random.uniform(60, 100), 2)
        })


def _generate_software(data: MockData):
    """生成 50 个软著"""
    for i in range(CONFIG["software_count"]):
        author = random.choice(data.teachers)
        rjzzbh = generate_software_id(i + 1)
        
        sw = {
            "id": i + 1, "rjzzbh": rjzzbh,
            "rjzzmc": f"{random.choice(['智慧','智能','云','数字'])}{random.choice(['校园','实验室','科研','教学','办公','安防','能源'])}{random.choice(['管理系统','监控平台','数据分析平台','协同平台','一站式服务平台'])}V{random.randint(1,5)}.{random.randint(0,9)}",
            "rjzzdjh": f"{random.randint(2022,2025)}SR{random.randint(1000000,9999999)}",
            "djrq": str(random_date()),
        }
        
        author_projects = [m for m in data.project_members if m["ry_gh"] == author["gh"]]
        sw["kybh"] = random.choice(author_projects)["kybh"] if author_projects and random.random() < 0.4 else None
        
        data.software.append(sw)
        data.software_members.append({
            "rjzzbh": rjzzbh, "zzryh": author["gh"], "zzxm": author["xm"], "smsx": 1
        })


def _generate_awards(data: MockData):
    """生成 60 个获奖"""
    for i in range(CONFIG["award_count"]):
        winner = random.choice(data.teachers)
        hj_date = random_date()
        # 教授更容易获高级别奖
        if winner["zc"] == "教授":
            level_w = [0.05,0.20,0.35,0.40]
        elif winner["zc"] == "副教授":
            level_w = [0.01,0.10,0.35,0.54]
        else:
            level_w = [0.00,0.02,0.20,0.78]
        hjjb = random.choices(AWARD_LEVELS, weights=level_w, k=1)[0]
        
        hjbh = generate_award_id(i + 1)
        award = {
            "id": i + 1, "hjbh": hjbh,
            "hjmc": f"{'国家' if hjjb == 'GJJ' else '省' if hjjb == 'SBJ' else '市'}级{random.choice(['自然科学','科技进步','技术发明','教学成果'])}{random.choice(['一等奖','二等奖','三等奖'])}",
            "hjjb": hjjb,
            "bjrq": str(hj_date),
            "bjdw": random.choice(["教育部","省教育厅","省科技厅","中国科协","省科协","市人民政府"]),
        }
        
        winner_projects = [m for m in data.project_members if m["ry_gh"] == winner["gh"]]
        award["kybh"] = random.choice(winner_projects)["kybh"] if winner_projects and random.random() < 0.5 else None
        
        data.awards.append(award)
        data.award_members.append({
            "hjbh": hjbh, "ry_gh": winner["gh"], "ry_xm": winner["xm"], "smsx": 1
        })
        # 加参与人
        others = [t for t in data.teachers if t["gh"] != winner["gh"]]
        n = random.choices([0,1,2,3,4,5], weights=[0.2,0.25,0.2,0.15,0.1,0.1], k=1)[0]
        selected = random.sample(others, min(n, len(others)))
        for j, t in enumerate(selected):
            data.award_members.append({
                "hjbh": hjbh, "ry_gh": t["gh"], "ry_xm": t["xm"], "smsx": j + 2
            })


def _generate_conferences(data: MockData):
    """生成 30 个学术会议"""
    for i in range(CONFIG["conference_count"]):
        host = random.choice(data.teachers)
        hy_date = random_date()
        hybh = generate_conference_id(i + 1)
        
        conf = {
            "id": i + 1, "hybh": hybh,
            "hymc": f"第{random.randint(1,20)}届{random.choice(['全国','国际','亚太','IEEE'])}{random.choice(['人工智能','计算机科学','材料科学','生物医学工程','能源与环境','数据科学'])}{random.choice(['学术年会','高峰论坛','研讨会'])}",
            "hydd": random.choice(["北京","上海","深圳","杭州","武汉","成都","西安","南京","广州"]),
            "hyqsrq": str(hy_date),
            "hyjzrq": str(hy_date + timedelta(days=random.randint(1, 5))),
            "hydj": random.choices(["GJ","GN","XX"], weights=[0.2,0.6,0.2], k=1)[0],
            "hyrs": random.randint(50, 500),
            "trjf": round(random.uniform(10000, 200000), 2),
            "zcr_gh": host["gh"],
            "lwps": random.randint(0, 200),
            "tybgps": random.randint(0, 10),
        }
        data.conferences.append(conf)


def _generate_institutions(data: MockData):
    """生成 15 个科研机构"""
    for i in range(CONFIG["institution_count"]):
        dept = DEPARTMENTS[i % len(DEPARTMENTS)]
        leader = random.choice([t for t in data.teachers if t["dw_bm"] == dept["code"]])
        jgbh = generate_institution_id(i + 1)
        
        inst = {
            "id": i + 1, "jgbh": jgbh,
            "jgmc": f"{dept['name']}{random.choice(['智能计算','先进材料','数据科学','新能源','生物医学','智能制造','数字媒体'])}{random.choice(['研究所','研究中心','重点实验室','工程中心'])}",
            "gkdwbm": dept["code"],
            "fzr_gh": leader["gh"],
            "xkmlm": f"{random.randint(7,12):02d}",
            "jglbm": random.choice(["SYS","YJS","GCS","QTLX"]),
            "jgjbm": random.choice(["GJJ","SBJ","XJ"]),
            "sfstjg": random.choice(["是","否"]),
        }
        data.institutions.append(inst)
        
        # 机构成员 — 3~10 个
        members_in_dept = [t for t in data.teachers if t["dw_bm"] == dept["code"]]
        n = random.randint(3, min(10, len(members_in_dept)))
        selected = random.sample(members_in_dept, n)
        for t in selected:
            data.institution_members.append({
                "jgbh": jgbh, "ry_gh": t["gh"], "ry_xm": t["xm"],
                "xkmlm": f"{random.randint(7,12):02d}",
                "yjfx": random.choice(["机器学习","计算机视觉","自然语言处理","生物信息学","量子计算","纳米材料","新能源材料","环境工程","智能制造","机器人学","信号处理","网络安全"]),
            })


def _print_summary(data: MockData):
    """打印生成摘要"""
    print(f"  教师: {len(data.teachers)} 人")
    print(f"  项目: {len(data.projects)} 个, 人员关系: {len(data.project_members)} 条")
    print(f"  经费到账: {len(data.fund_arrivals)} 条, 支出: {len(data.fund_expenses)} 条, 外拨: {len(data.fund_transfers)} 条")
    print(f"  论文: {len(data.papers)} 篇, 作者: {len(data.paper_authors)} 人次")
    print(f"  专利: {len(data.patents)} 项, 发明人: {len(data.patent_inventors)} 人次")
    print(f"  著作: {len(data.books)} 本, 作者: {len(data.book_authors)} 人次")
    print(f"  软著: {len(data.software)} 项, 成员: {len(data.software_members)} 人次")
    print(f"  获奖: {len(data.awards)} 项, 人员: {len(data.award_members)} 人次")
    print(f"  会议: {len(data.conferences)} 个")
    print(f"  科研机构: {len(data.institutions)} 个, 成员: {len(data.institution_members)} 人次")
