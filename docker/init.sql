-- ============================================
-- 教师个人科研查询器 — MySQL 初始化脚本
-- 数据集：GXKY 科研管理数据集
-- 遵循：高校科研管理数据标准
-- ============================================

USE teacher_research;

-- ============================================
-- 0. 教职工基本信息（教师身份主表）
-- 来源：人事管理数据集，作为本系统的用户关联表
-- ============================================
CREATE TABLE IF NOT EXISTS t_jzg_jbxx (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    gh           VARCHAR(50)  NOT NULL UNIQUE COMMENT '工号',
    xm           VARCHAR(100) NOT NULL COMMENT '姓名',
    xb           VARCHAR(10)  COMMENT '性别（男/女）',
    dw_bm        VARCHAR(50)  COMMENT '所属单位编码',
    dw_mc        VARCHAR(200) COMMENT '所属单位名称',
    zc           VARCHAR(50)  COMMENT '职称（教授/副教授/讲师/助教）',
    xkml_bm      VARCHAR(10)  COMMENT '学科门类码',
    ryrq         DATE         COMMENT '入校日期',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_gh (gh),
    INDEX idx_dept (dw_bm)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教职工基本信息';

-- ============================================
-- 1. 科研项目基本信息
-- 来源：数据标准 GXKY0201 → T_GXKY_KYXMJBXX
-- 业务描述：记录科研项目的基本信息
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_xmjbxx (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    kybh         VARCHAR(100)  NOT NULL COMMENT '科研项目编号（学校自编）',
    xmmc         VARCHAR(500)  NOT NULL COMMENT '项目名称',
    xmbh_xn      VARCHAR(100)  COMMENT '校内编号',
    ssdw_bm      VARCHAR(50)   COMMENT '所属单位编码（需与人事处组织机构编码一致）',
    xmlx_bm      VARCHAR(20)   COMMENT '项目来源码（NSFC国家基金委/MOST科技部/MOE教育部/PROV省科技厅/ENTERPRISE企业/OTHER其他）',
    xmxz_bm      VARCHAR(20)   COMMENT '项目性质码（ZX纵向/HX横向）',
    xmlb_bm      VARCHAR(20)   COMMENT '项目类别码（重大/重点/面上/青年/其他）',
    xmjb_bm      VARCHAR(20)   COMMENT '项目级别码（GJJZD国家级重点/GJJYB国家级一般/SBJZD省部级重点/SBJYB省部级一般/TJYB厅局级/QYWT企业委托）',
    xkml_bm      VARCHAR(10)   COMMENT '学科门类码',
    lxrq         DATE          COMMENT '立项日期',
    ksrq         DATE          COMMENT '开始日期',
    jxrq         DATE          COMMENT '结项日期',
    jhwcrq       DATE          COMMENT '计划完成日期',
    fzr_gh       VARCHAR(50)   COMMENT '项目负责人工号',
    ht_jf        DECIMAL(18,2) DEFAULT 0.00 COMMENT '合同经费（元）',
    pt_jf        DECIMAL(18,2) DEFAULT 0.00 COMMENT '配套经费（元）',
    zxzt_bm      VARCHAR(20)   DEFAULT 'ZAIYAN' COMMENT '执行状态码（ZAIYAN在研/JIETI结题/ZHONGZHI中止）',
    htbh         VARCHAR(100)  COMMENT '合同编号',
    jfkh         VARCHAR(50)   COMMENT '经费卡号（关联财务系统）',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_fzr    (fzr_gh),
    INDEX idx_status (zxzt_bm),
    INDEX idx_level  (xmjb_bm),
    INDEX idx_dept   (ssdw_bm),
    INDEX idx_date   (lxrq)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科研项目基本信息';

-- ============================================
-- 2. 科研项目人员关系（核心枢纽表）
-- 来源：数据标准 GXKY0202 → T_GXKY_KYXMRYXX
-- 业务描述：记录科研项目参与人员，通过此表可关联教师和所有项目/成果
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_xmry (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    kybh         VARCHAR(100) NOT NULL COMMENT '科研项目编号',
    ry_gh        VARCHAR(50)  NOT NULL COMMENT '人员工号（本校教师填工号、学生填学号、校外填编号）',
    ry_xm        VARCHAR(100) COMMENT '人员姓名',
    dw_bm        VARCHAR(50)  COMMENT '单位编码',
    rylx_bm      VARCHAR(20)  DEFAULT 'BXJS' COMMENT '人员类型码（BXJS本校教师/BXYJS本校研究生/XX校外）',
    ryjs_bm      VARCHAR(20)  DEFAULT 'CYR'  COMMENT '人员角色码（FZR负责人/CYR参与人/KYMS科研秘书）',
    smsx         INT          DEFAULT 1     COMMENT '署名顺序（1=项目负责人，排名第一为项目负责人）',
    gxl          DECIMAL(5,2) DEFAULT 0.00  COMMENT '贡献率（%）',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ky_ry (kybh, ry_gh),
    INDEX idx_ry (ry_gh),
    INDEX idx_ky (kybh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科研项目人员关系';

-- ============================================
-- 3. 科研经费到账明细
-- 来源：数据标准 GXKY0204 → T_GXKY_KYXMJFDZMXXX
-- 业务描述：经费到账数据，真正源头在财务处
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_jfdz (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    cw_xmbh      VARCHAR(100) COMMENT '财务项目编号',
    kybh         VARCHAR(100) NOT NULL COMMENT '科研项目编号',
    km_bh        VARCHAR(50)  COMMENT '科目编号',
    km_mc        VARCHAR(200) COMMENT '科目名称',
    kj_nd        VARCHAR(4)   COMMENT '会计年度（YYYY）',
    pz_rq        DATE         COMMENT '凭证日期（即到账日期）',
    dz_je        DECIMAL(18,2) DEFAULT 0.00 COMMENT '贷金额/到账金额（元）',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ky   (kybh),
    INDEX idx_year (kj_nd),
    INDEX idx_date (pz_rq)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科研经费到账明细';

-- ============================================
-- 4. 科研经费支出明细
-- 来源：数据标准 GXKY0205 → T_GXKY_KYXMJFZCMXXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_jfzc (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    cw_xmbh      VARCHAR(100) COMMENT '财务项目编号',
    kybh         VARCHAR(100) NOT NULL COMMENT '科研项目编号',
    km_bh        VARCHAR(50)  COMMENT '科目编号',
    km_mc        VARCHAR(200) COMMENT '科目名称（SBF设备费/CLF材料费/CLF测试费/CHF差旅费/HYF会议费/其他）',
    kj_nd        VARCHAR(4)   COMMENT '会计年度（YYYY）',
    pz_rq        DATE         COMMENT '凭证日期（即支出日期）',
    zc_je        DECIMAL(18,2) DEFAULT 0.00 COMMENT '借金额/支出金额（元）',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ky   (kybh),
    INDEX idx_year (kj_nd)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科研经费支出明细';

-- ============================================
-- 5. 科研经费外拨明细
-- 来源：数据标准 GXKY0206 → T_GXKY_KYXMJFWBMXXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_jfwb (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    cw_xmbh      VARCHAR(100) COMMENT '财务项目编号',
    kybh         VARCHAR(100) NOT NULL COMMENT '科研项目编号',
    km_bh        VARCHAR(50)  COMMENT '科目编号',
    km_mc        VARCHAR(200) COMMENT '科目名称',
    kj_nd        VARCHAR(4)   COMMENT '会计年度（YYYY）',
    pz_rq        DATE         COMMENT '凭证日期',
    wb_je        DECIMAL(18,2) DEFAULT 0.00 COMMENT '外拨金额（元）',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ky (kybh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科研经费外拨明细';

-- ============================================
-- 6. 科研著作基本信息
-- 来源：数据标准 GXKY0301 → T_GXKY_KYZZJBXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_zz (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    zzbh         VARCHAR(100) NOT NULL UNIQUE COMMENT '著作编号',
    zzmc         VARCHAR(300) COMMENT '著作名称',
    zzywmc       VARCHAR(300) COMMENT '著作英文名称',
    cbs          VARCHAR(200) COMMENT '出版社',
    cbd          VARCHAR(100) COMMENT '出版地',
    cbsjbm       VARCHAR(20)  COMMENT '出版社级别码',
    cbrq         DATE         COMMENT '出版日期',
    isbn         VARCHAR(50)  COMMENT 'ISBN号',
    zzzs         INT          COMMENT '著作字数（千字）',
    lzlbm        VARCHAR(20)  COMMENT '论著类别码（ZZ专著/JC教材/YZ译著/其他）',
    yzm          VARCHAR(20)  COMMENT '语种码（CN中文/EN英文/其他）',
    sfsmbx       VARCHAR(10)  COMMENT '是否署名本校（是/否）',
    kybh         VARCHAR(100) COMMENT '关联科研项目编号',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (cbrq),
    INDEX idx_ky (kybh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科研著作基本信息';

-- ============================================
-- 7. 著作作者关联
-- 来源：数据标准 GXKY0302 → T_GXKY_KYZZZZXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_zzzz (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    zzbh         VARCHAR(100) NOT NULL COMMENT '著作编号',
    zzryh        VARCHAR(50)  NOT NULL COMMENT '作者人员号（教师工号/校外编号）',
    zzxm         VARCHAR(100) COMMENT '作者姓名',
    cdjs         VARCHAR(50)  COMMENT '承担角色（ZB主编/FZB副主编/CB参编）',
    smsx         INT          DEFAULT 1 COMMENT '署名顺序',
    gxl          DECIMAL(5,2) DEFAULT 0.00 COMMENT '贡献率（%）',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_zz_ry (zzbh, zzryh),
    INDEX idx_ry (zzryh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='著作作者关联';

-- ============================================
-- 8. 科研专利基本信息
-- 来源：数据标准 GXKY0303 → T_GXKY_KYZLJBXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_zl (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    zlbh         VARCHAR(100) NOT NULL UNIQUE COMMENT '专利编号',
    zlmc         VARCHAR(300) COMMENT '专利名称',
    zllx         VARCHAR(20)  COMMENT '专利类型（FM发明/SY实用新型/WG外观设计）',
    zlzt         VARCHAR(20)  DEFAULT 'YX' COMMENT '专利状态（YX有效/SQ申请中/SX失效）',
    sqrq         DATE         COMMENT '申请日期',
    sqrq2        DATE         COMMENT '授权日期',
    zldlr        VARCHAR(200) COMMENT '专利代理机构',
    kybh         VARCHAR(100) COMMENT '关联科研项目编号',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (zllx),
    INDEX idx_date (sqrq)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科研专利基本信息';

-- ============================================
-- 9. 专利发明人关联
-- 来源：数据标准 GXKY0304 → T_GXKY_KYZLFMRXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_zlfmr (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    zlbh         VARCHAR(100) NOT NULL COMMENT '专利编号',
    fmr_gh       VARCHAR(50)  NOT NULL COMMENT '发明人工号',
    fmr_xm       VARCHAR(100) COMMENT '发明人姓名',
    smsx         INT          DEFAULT 1 COMMENT '署名顺序',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_zl_ry (zlbh, fmr_gh),
    INDEX idx_ry (fmr_gh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='专利发明人关联';

-- ============================================
-- 10. 软件著作基本信息
-- 来源：数据标准 GXKY0305 → T_GXKY_RJZZJBXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_rjzz (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    rjzzbh       VARCHAR(100) NOT NULL UNIQUE COMMENT '软件著作编号',
    rjzzmc       VARCHAR(300) COMMENT '软件著作名称',
    rjzzqlxm     VARCHAR(20)  COMMENT '软件著作权类型码',
    rjzzdjh      VARCHAR(100) COMMENT '软件著作登记号',
    djrq         DATE         COMMENT '登记日期',
    kybh         VARCHAR(100) COMMENT '关联科研项目编号',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ky (kybh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='软件著作基本信息';

-- ============================================
-- 11. 软件著作成员关联
-- 来源：数据标准 GXKY0306 → T_GXKY_RJZZCYXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_rjzzcy (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    rjzzbh       VARCHAR(100) NOT NULL COMMENT '软件著作编号',
    zzryh        VARCHAR(50)  NOT NULL COMMENT '著作人员号',
    zzxm         VARCHAR(100) COMMENT '著作人姓名',
    smsx         INT          DEFAULT 1 COMMENT '署名顺序',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_rj_ry (rjzzbh, zzryh),
    INDEX idx_ry (zzryh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='软件著作成员关联';

-- ============================================
-- 12. 科研获奖成果基本信息
-- 来源：数据标准 GXKY0307 → T_GXKY_KYHJCGJBXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_hj (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    hjbh         VARCHAR(100) NOT NULL UNIQUE COMMENT '获奖编号',
    hjmc         VARCHAR(500) COMMENT '获奖名称',
    hjjb         VARCHAR(20)  COMMENT '获奖级别（GJJ国家级/SBJ省部级/TJ厅局级/XJ校级）',
    hjlb         VARCHAR(50)  COMMENT '获奖类别（ZRKXJ自然科学奖/JSFMJ技术发明奖/KJJBP科技进步奖/其他）',
    hjrq         DATE         COMMENT '获奖日期',
    bjdw         VARCHAR(200) COMMENT '颁奖单位',
    kybh         VARCHAR(100) COMMENT '关联科研项目编号',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_level (hjjb),
    INDEX idx_date  (hjrq)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科研获奖成果基本信息';

-- ============================================
-- 13. 获奖人员关联
-- 来源：数据标准 GXKY0308 → T_GXKY_KYHJCGCYXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_hjry (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    hjbh         VARCHAR(100) NOT NULL COMMENT '获奖编号',
    ry_gh        VARCHAR(50)  NOT NULL COMMENT '人员工号',
    ry_xm        VARCHAR(100) COMMENT '人员姓名',
    smsx         INT          DEFAULT 1 COMMENT '署名顺序',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_hj_ry (hjbh, ry_gh),
    INDEX idx_ry (ry_gh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='获奖人员关联';

-- ============================================
-- 14. 科技论文基本信息
-- 来源：数据标准 GXKY0309 → T_GXKY_KJLWJBXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_lw (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    lwbh         VARCHAR(100) NOT NULL UNIQUE COMMENT '论文编号',
    lwmc         VARCHAR(500) COMMENT '论文名称',
    lwywmc       VARCHAR(500) COMMENT '论文英文名称',
    kwmc         VARCHAR(300) COMMENT '刊物名称',
    kwjb         VARCHAR(20)  COMMENT '刊物级别（SCI-1/SCI-2/SCI-3/SCI-4/EI/CORE中文核心/OTHER其他）',
    slqk         VARCHAR(100) COMMENT '收录情况',
    fbn          VARCHAR(4)   COMMENT '发表年号',
    fbq          VARCHAR(10)  COMMENT '发表期号',
    lwzs         INT          COMMENT '论文字数',
    xkml_bm      VARCHAR(10)  COMMENT '学科门类码',
    kybh         VARCHAR(100) COMMENT '关联科研项目编号',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_year  (fbn),
    INDEX idx_level (kwjb)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科技论文基本信息';

-- ============================================
-- 15. 论文作者关联
-- 来源：数据标准 GXKY0310 → T_GXKY_KJLWZZXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_lwzz (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    lwbh         VARCHAR(100) NOT NULL COMMENT '论文编号',
    zzgh         VARCHAR(50)  NOT NULL COMMENT '作者工号',
    zzxm         VARCHAR(100) COMMENT '作者姓名',
    dwbm         VARCHAR(50)  COMMENT '单位编码',
    smsx         INT          DEFAULT 1 COMMENT '署名顺序（1=第一作者）',
    gxl          DECIMAL(5,2) DEFAULT 0.00 COMMENT '贡献率（%）',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_lw_zz (lwbh, zzgh),
    INDEX idx_zz   (zzgh),
    INDEX idx_lw   (lwbh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='论文作者关联';

-- ============================================
-- 16. 学术会议信息
-- 来源：数据标准 GXKY0401 → T_GXKY_KYXSHYXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_xshy (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    hybh         VARCHAR(100) NOT NULL UNIQUE COMMENT '会议编号',
    hymc         VARCHAR(300) COMMENT '会议名称',
    hyywmc       VARCHAR(300) COMMENT '会议英文名称',
    hydd         VARCHAR(200) COMMENT '会议地点',
    hyqsrq       DATE         COMMENT '会议起始日期',
    hyjzrq       DATE         COMMENT '会议终止日期',
    hydj         VARCHAR(20)  COMMENT '会议等级码（GJ国际/GN国内/XX校级）',
    hyrs         INT          COMMENT '会议人数',
    trjf         DECIMAL(18,2) DEFAULT 0.00 COMMENT '投入经费（元）',
    zcr_gh       VARCHAR(50)  COMMENT '主持人工号',
    lwps         INT          DEFAULT 0 COMMENT '论文篇数',
    tybgps       INT          DEFAULT 0 COMMENT '特邀报告篇数',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (hyqsrq),
    INDEX idx_rcr  (zcr_gh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学术会议信息';

-- ============================================
-- 17. 科研机构基本信息
-- 来源：数据标准 GXKY0101 → T_GXKY_KYJGJBXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_kyjg (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    jgbh         VARCHAR(100) NOT NULL UNIQUE COMMENT '科研机构编号',
    jgmc         VARCHAR(200) COMMENT '科研机构名称',
    gkdwbm       VARCHAR(50)  COMMENT '挂靠单位编码（需与人事处组织机构编码一致）',
    fzr_gh       VARCHAR(50)  COMMENT '负责人工号',
    xkmlm        VARCHAR(10)  COMMENT '学科门类码',
    jglbm        VARCHAR(20)  COMMENT '机构类别码',
    jgjbm        VARCHAR(20)  COMMENT '机构级别码',
    sfstjg       VARCHAR(10)  COMMENT '是否实体机构（是/否）',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fzr (fzr_gh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科研机构基本信息';

-- ============================================
-- 18. 科研机构人员关联
-- 来源：数据标准 GXKY0102 → T_GXKY_KYJGRYXX
-- ============================================
CREATE TABLE IF NOT EXISTS t_ky_kyjgry (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    jgbh         VARCHAR(100) NOT NULL COMMENT '科研机构编号',
    ry_gh        VARCHAR(50)  NOT NULL COMMENT '人员工号（校内教师需与人事处工号一致）',
    ry_xm        VARCHAR(100) COMMENT '人员姓名',
    xkmlm        VARCHAR(10)  COMMENT '学科门类码',
    yjfx         VARCHAR(200) COMMENT '研究方向',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_jg_ry (jgbh, ry_gh),
    INDEX idx_ry (ry_gh)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科研机构人员关联';

-- ============================================
-- 完成标记
-- ============================================
SELECT '=== GXKY 科研管理数据集 18张表创建完成 ===' AS result;
SELECT TABLE_NAME, TABLE_COMMENT 
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'teacher_research' 
ORDER BY TABLE_NAME;
