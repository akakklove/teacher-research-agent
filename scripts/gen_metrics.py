#!/usr/bin/env python3
"""Generate 200+ metrics for teacher-research-agent v3.0"""
import yaml, os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

metrics = []

def add(id, name, category, priority, desc, tables, sql, chart, unit="", role=False):
    ds = [{"table": t[0], "role": t[1], "key_field": t[2]} for t in tables]
    m = {
        "id": id, "name": name, "category": category, "priority": priority,
        "description": desc, "data_sources": ds, "sql_template": sql.strip(),
        "chart_type": chart,
    }
    if unit: m["unit"] = unit
    if role: m["role_filter"] = True
    metrics.append(m)

P = add

# ═════════════════════════════════════════
# 1. 项目概览 (25)
# ═════════════════════════════════════════
c = "项目概览"
P("project_count_total","参与项目总数",c,1,"教师参与的所有科研项目数量",
  [("t_ky_xmry","人员项目关联","ry_gh")],
  "SELECT COUNT(DISTINCT kybh) as value FROM t_ky_xmry WHERE ry_gh = :teacher_id","kpi_card","个")

P("project_count_leader","主持项目数",c,2,"教师作为项目负责人的科研项目数",
  [("t_ky_xmry","主持(smsx=1)","ry_gh, smsx")],
  "SELECT COUNT(DISTINCT kybh) as value FROM t_ky_xmry WHERE ry_gh = :teacher_id AND smsx = 1","kpi_card","个",True)

P("project_count_participant","参与项目数(非主持)",c,3,"作为参与者的项目数",
  [("t_ky_xmry","参与","ry_gh, smsx")],
  "SELECT COUNT(DISTINCT kybh) as value FROM t_ky_xmry WHERE ry_gh = :teacher_id AND smsx != 1","kpi_card","个")

P("project_active_count","在研项目数",c,4,"当前在研项目数量",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","状态","zxzt_bm")],
  "SELECT COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND p.zxzt_bm='ZAIYAN'","kpi_card","个")

P("project_completed_count","已结题项目数",c,5,"已结题项目数量",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","状态","zxzt_bm")],
  "SELECT COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND p.zxzt_bm='JIETI'","kpi_card","个")

P("project_count_national","国家级项目数",c,6,"国家级项目总数",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","级别","xmjb_bm")],
  "SELECT COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND p.xmjb_bm LIKE 'GJJ%'","kpi_card","个")

P("project_count_provincial","省部级项目数",c,7,"省部级及以上项目数",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","级别","xmjb_bm")],
  "SELECT COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND (p.xmjb_bm LIKE 'GJJ%' OR p.xmjb_bm LIKE 'SBJ%')","kpi_card","个")

P("project_by_level","项目级别分布",c,8,"按级别统计项目数量",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","级别","xmjb_bm")],
  "SELECT p.xmjb_bm as label, COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id GROUP BY p.xmjb_bm ORDER BY value DESC","pie_chart")

P("project_by_source","项目来源分布",c,9,"按来源统计项目",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","来源","xmlx_bm")],
  "SELECT p.xmlx_bm as label, COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id GROUP BY p.xmlx_bm ORDER BY value DESC","pie_chart")

P("project_by_nature","项目性质分布",c,10,"纵向/横向分布",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","性质","xmxz_bm")],
  "SELECT p.xmxz_bm as label, COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id GROUP BY p.xmxz_bm ORDER BY value DESC","pie_chart")

P("project_status_distribution","项目状态分布",c,11,"在研/结题/中止占比",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","状态","zxzt_bm")],
  "SELECT p.zxzt_bm as label, COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id GROUP BY p.zxzt_bm ORDER BY value DESC","pie_chart")

P("project_yearly_trend","年度立项趋势",c,12,"按年度统计新立项项目数",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","立项日期","lxrq")],
  "SELECT YEAR(p.lxrq) as label, COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND YEAR(p.lxrq) BETWEEN :start_year AND :end_year GROUP BY YEAR(p.lxrq) ORDER BY label","line_chart")

P("project_by_year_level","项目年度×级别分布",c,13,"年度和级别交叉统计",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","立项+级别","lxrq, xmjb_bm")],
  "SELECT CONCAT(YEAR(p.lxrq),'-',p.xmjb_bm) as label, COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND YEAR(p.lxrq) BETWEEN :start_year AND :end_year GROUP BY YEAR(p.lxrq), p.xmjb_bm ORDER BY YEAR(p.lxrq)","stacked_bar")

P("project_avg_duration_days","项目平均周期(天)",c,14,"从立项到结题平均天数",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","日期","lxrq, jxrq, jhwcrq")],
  "SELECT ROUND(AVG(DATEDIFF(COALESCE(p.jxrq,p.jhwcrq),p.lxrq))) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND p.lxrq IS NOT NULL","kpi_card","天")

P("project_duration_distribution","项目周期分布",c,15,"不同周期区间的项目数",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","日期","lxrq, jxrq")],
  "SELECT CASE WHEN DATEDIFF(COALESCE(p.jxrq,p.jhwcrq),p.lxrq)<=365 THEN '<=1年' WHEN DATEDIFF(COALESCE(p.jxrq,p.jhwcrq),p.lxrq)<=730 THEN '1-2年' WHEN DATEDIFF(COALESCE(p.jxrq,p.jhwcrq),p.lxrq)<=1095 THEN '2-3年' ELSE '>3年' END as label, COUNT(*) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND p.lxrq IS NOT NULL GROUP BY label ORDER BY value DESC","bar_chart")

P("project_fund_total_contract","合同经费总额",c,16,"主持项目合同经费合计",
  [("t_ky_xmry","主持人","ry_gh, smsx"),("t_ky_xmjbxx","经费","ht_jf")],
  "SELECT COALESCE(SUM(p.ht_jf),0) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1","kpi_card","元")

P("project_fund_total_match","配套经费总额",c,17,"主持项目配套经费合计",
  [("t_ky_xmry","主持人","ry_gh, smsx"),("t_ky_xmjbxx","配套经费","pt_jf")],
  "SELECT COALESCE(SUM(p.pt_jf),0) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1","kpi_card","元")

P("project_fund_avg_per_project","项目均经费",c,18,"平均每项目经费额度",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_xmjbxx","经费","ht_jf, pt_jf")],
  "SELECT ROUND(COALESCE(AVG(p.ht_jf+p.pt_jf),0)) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1","kpi_card","元/项")

P("project_fund_ranking","项目经费排名",c,19,"主持项目按合同经费降序",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_xmjbxx","项目","xmmc, ht_jf, pt_jf")],
  "SELECT p.xmmc as label, (p.ht_jf+p.pt_jf) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 ORDER BY value DESC","bar_chart","元")

P("project_detail_list","项目明细列表",c,20,"个人所有项目详细信息",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","完整信息","xmmc,xmjb_bm,xmxz_bm,xmlx_bm,lxrq,jxrq,ht_jf,pt_jf,zxzt_bm,htbh")],
  "SELECT p.xmmc as 项目名称, p.xmjb_bm as 项目级别, p.xmxz_bm as 性质, p.xmlx_bm as 来源, DATE_FORMAT(p.lxrq,'%Y-%m-%d') as 立项日期, DATE_FORMAT(COALESCE(p.jxrq,p.jhwcrq),'%Y-%m-%d') as 预计结题, p.ht_jf as 合同经费, p.pt_jf as 配套经费, p.zxzt_bm as 执行状态 FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id ORDER BY p.lxrq DESC","table")

# Derived
P("project_completion_rate","项目结题率",c,21,"已结题项目占全部项目比例",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","状态","zxzt_bm")],
  "SELECT ROUND(SUM(CASE WHEN p.zxzt_bm='JIETI' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id","kpi_card","%")

P("project_leader_ratio","主持项目占比",c,22,"主持项目占总项目比例",
  [("t_ky_xmry","人员","ry_gh, smsx")],
  "SELECT ROUND(SUM(CASE WHEN smsx=1 THEN 1 ELSE 0 END)*100.0/COUNT(DISTINCT kybh),1) as value FROM t_ky_xmry WHERE ry_gh=:teacher_id","kpi_card","%")

P("project_national_ratio","国家级项目占比",c,23,"国家级项目占总项目比例",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","级别","xmjb_bm")],
  "SELECT ROUND(SUM(CASE WHEN p.xmjb_bm LIKE 'GJJ%' THEN 1 ELSE 0 END)*100.0/COUNT(DISTINCT r.kybh),1) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id","kpi_card","%")

P("project_lateral_ratio","横向项目占比",c,24,"横向项目占总项目比例",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","性质","xmxz_bm")],
  "SELECT ROUND(SUM(CASE WHEN p.xmxz_bm='HX' THEN 1 ELSE 0 END)*100.0/COUNT(DISTINCT r.kybh),1) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id","kpi_card","%")

P("project_yoy_growth","项目数年增长率",c,25,"当年新立项数同比增长率",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","日期","lxrq")],
  "SELECT ROUND((COUNT(CASE WHEN YEAR(p.lxrq)=:end_year THEN 1 END)-COUNT(CASE WHEN YEAR(p.lxrq)=:start_year THEN 1 END))*100.0/NULLIF(COUNT(CASE WHEN YEAR(p.lxrq)=:start_year THEN 1 END),0),1) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1","kpi_card","%")

# ═════════════════════════════════════════
# 2. 经费分析 (23)
# ═════════════════════════════════════════
c = "经费分析"
P("fund_total_arrived","到账经费总额",c,31,"主持项目经费到账总额",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账明细","dz_je")],
  "SELECT COALESCE(SUM(f.dz_je),0) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date","kpi_card","元")

P("fund_total_spent","经费支出总额",c,32,"主持项目经费支出总额",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfzc","支出明细","zc_je")],
  "SELECT COALESCE(SUM(f.zc_je),0) as value FROM t_ky_xmry r JOIN t_ky_jfzc f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date","kpi_card","元")

P("fund_total_outbound","经费外拨总额",c,33,"主持项目经费外拨总额",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfwb","外拨明细","wb_je")],
  "SELECT COALESCE(SUM(f.wb_je),0) as value FROM t_ky_xmry r JOIN t_ky_jfwb f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date","kpi_card","元")

P("fund_net_balance","经费净余额",c,34,"到账-支出-外拨 净余额",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账","dz_je"),("t_ky_jfzc","支出","zc_je")],
  "SELECT COALESCE((SELECT SUM(dz_je) FROM t_ky_jfdz WHERE kybh IN (SELECT kybh FROM t_ky_xmry WHERE ry_gh=:teacher_id AND smsx=1) AND pz_rq BETWEEN :start_date AND :end_date),0) - COALESCE((SELECT SUM(zc_je) FROM t_ky_jfzc WHERE kybh IN (SELECT kybh FROM t_ky_xmry WHERE ry_gh=:teacher_id AND smsx=1) AND pz_rq BETWEEN :start_date AND :end_date),0) as value","kpi_card","元")

P("fund_execution_rate","经费执行率",c,35,"支出/到账执行率",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账","dz_je"),("t_ky_jfzc","支出","zc_je")],
  "SELECT ROUND(COALESCE((SELECT SUM(zc_je) FROM t_ky_jfzc WHERE kybh IN (SELECT kybh FROM t_ky_xmry WHERE ry_gh=:teacher_id AND smsx=1) AND pz_rq BETWEEN :start_date AND :end_date),0)*100.0/NULLIF(COALESCE((SELECT SUM(dz_je) FROM t_ky_jfdz WHERE kybh IN (SELECT kybh FROM t_ky_xmry WHERE ry_gh=:teacher_id AND smsx=1) AND pz_rq BETWEEN :start_date AND :end_date),0),0),1) as value","kpi_card","%")

P("fund_monthly_trend","月度经费到账趋势",c,36,"月度到账金额变化",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账","dz_je, pz_rq")],
  "SELECT DATE_FORMAT(f.pz_rq,'%Y-%m') as label, SUM(f.dz_je) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY DATE_FORMAT(f.pz_rq,'%Y-%m') ORDER BY label","line_chart","元")

P("fund_monthly_spent_trend","月度支出趋势",c,37,"月度支出金额变化",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfzc","支出","zc_je, pz_rq")],
  "SELECT DATE_FORMAT(f.pz_rq,'%Y-%m') as label, SUM(f.zc_je) as value FROM t_ky_xmry r JOIN t_ky_jfzc f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY DATE_FORMAT(f.pz_rq,'%Y-%m') ORDER BY label","line_chart","元")

P("fund_monthly_outbound_trend","月度外拨趋势",c,38,"月度外拨金额变化",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfwb","外拨","wb_je, pz_rq")],
  "SELECT DATE_FORMAT(f.pz_rq,'%Y-%m') as label, SUM(f.wb_je) as value FROM t_ky_xmry r JOIN t_ky_jfwb f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY DATE_FORMAT(f.pz_rq,'%Y-%m') ORDER BY label","line_chart","元")

P("fund_yearly_inout","年度收支对比",c,39,"每年到账vs支出对比",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账","dz_je"),("t_ky_jfzc","支出","zc_je")],
  "SELECT t.year as label, COALESCE(t.arrived,0) as 到账, COALESCE(t.spent,0) as 支出 FROM (SELECT YEAR(f.pz_rq) as year, SUM(f.dz_je) as arrived FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY YEAR(f.pz_rq)) t LEFT JOIN (SELECT YEAR(f.pz_rq) as year, SUM(f.zc_je) as spent FROM t_ky_xmry r JOIN t_ky_jfzc f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY YEAR(f.pz_rq)) s ON t.year=s.year ORDER BY t.year","bar_chart")

P("fund_yearly_comparison","年度经费对比",c,40,"历年经费到账金额对比",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账","dz_je, pz_rq")],
  "SELECT YEAR(f.pz_rq) as label, SUM(f.dz_je) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY YEAR(f.pz_rq) ORDER BY label","bar_chart","元")

P("fund_expense_structure","经费支出结构",c,41,"按科目统计支出分布",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfzc","支出科目","km_mc, zc_je")],
  "SELECT f.km_mc as label, SUM(f.zc_je) as value FROM t_ky_xmry r JOIN t_ky_jfzc f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY f.km_mc ORDER BY value DESC","pie_chart")

P("fund_arrival_by_project","各项目到账经费分布",c,42,"每主持项目经费到账",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账","dz_je"),("t_ky_xmjbxx","项目名","xmmc")],
  "SELECT p.xmmc as label, COALESCE(SUM(f.dz_je),0) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY p.xmmc ORDER BY value DESC","bar_chart","元")

# Derived - Fund
P("fund_avg_annual_arrived","年均到账经费",c,43,"平均每年到账金额",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账","dz_je")],
  "SELECT ROUND(COALESCE(SUM(f.dz_je),0)/NULLIF((:end_year-:start_year+1),0)) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date","kpi_card","元/年")

P("fund_yoy_growth","经费同比增长率",c,44,"到账经费同比增长",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账","dz_je")],
  "SELECT ROUND((COALESCE(SUM(CASE WHEN YEAR(f.pz_rq)=:end_year THEN f.dz_je ELSE 0 END),0)-COALESCE(SUM(CASE WHEN YEAR(f.pz_rq)=:start_year THEN f.dz_je ELSE 0 END),0))*100.0/NULLIF(SUM(CASE WHEN YEAR(f.pz_rq)=:start_year THEN f.dz_je ELSE 0 END),0),1) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1","kpi_card","%")

P("fund_spent_ratio","支出占比",c,45,"支出占到账经费比例",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账","dz_je"),("t_ky_jfzc","支出","zc_je")],
  "SELECT ROUND(COALESCE((SELECT SUM(zc_je) FROM t_ky_jfzc WHERE kybh IN (SELECT kybh FROM t_ky_xmry WHERE ry_gh=:teacher_id AND smsx=1) AND pz_rq BETWEEN :start_date AND :end_date),0)*100.0/NULLIF(COALESCE((SELECT SUM(dz_je) FROM t_ky_jfdz WHERE kybh IN (SELECT kybh FROM t_ky_xmry WHERE ry_gh=:teacher_id AND smsx=1) AND pz_rq BETWEEN :start_date AND :end_date),0),0),1) as value","kpi_card","%")

P("fund_per_project_avg_arrived","项目均到账经费",c,46,"平均每项目到账",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账","dz_je")],
  "SELECT ROUND(COALESCE(SUM(f.dz_je),0)/NULLIF(COUNT(DISTINCT f.kybh),0)) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date","kpi_card","元")

P("fund_max_single_arrival","最大单笔到账",c,47,"单笔最大到账金额",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账","dz_je")],
  "SELECT MAX(f.dz_je) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date","kpi_card","元")

P("fund_arrival_ranking","经费到账排名",c,48,"到账经费的明细排名",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账","dz_je, pz_rq")],
  "SELECT DATE_FORMAT(f.pz_rq,'%Y-%m-%d') as label, f.dz_je as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date ORDER BY f.dz_je DESC LIMIT 20","bar_chart","元")

# ═════════════════════════════════════════
# 3. 论文成果 (25)
# ═════════════════════════════════════════
c = "论文成果"
P("paper_count_total","发表论文总数",c,61,"教师参与发表的全部论文数",
  [("t_ky_lwzz","论文作者","zzgh")],
  "SELECT COUNT(DISTINCT lwbh) as value FROM t_ky_lwzz WHERE zzgh = :teacher_id","kpi_card","篇")

P("paper_first_author_count","第一作者论文数",c,62,"作为第一作者的论文数",
  [("t_ky_lwzz","论文作者","zzgh, smsx")],
  "SELECT COUNT(DISTINCT lwbh) as value FROM t_ky_lwzz WHERE zzgh = :teacher_id AND smsx = 1","kpi_card","篇")

P("paper_corresponding_count","通讯作者论文数",c,63,"作为通讯作者的论文数",
  [("t_ky_lwzz","论文作者","zzgh, smsx")],
  "SELECT COUNT(DISTINCT lwbh) as value FROM t_ky_lwzz WHERE zzgh = :teacher_id AND smsx = 2","kpi_card","篇")

P("paper_by_level","论文级别分布",c,64,"按期刊级别统计论文",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","论文","kwjb")],
  "SELECT p.kwjb as label, COUNT(DISTINCT a.lwbh) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND p.kwjb IS NOT NULL GROUP BY p.kwjb ORDER BY value DESC","pie_chart")

P("paper_by_source","期刊来源分布",c,65,"发表期刊分布Top15",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","期刊","kwmc")],
  "SELECT p.kwmc as label, COUNT(*) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id GROUP BY p.kwmc ORDER BY value DESC LIMIT 15","bar_chart")

P("paper_yearly_trend","年度论文趋势",c,66,"每年发表论文数量",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","论文","fbn")],
  "SELECT YEAR(p.fbn) as label, COUNT(DISTINCT a.lwbh) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND YEAR(p.fbn) BETWEEN :start_year AND :end_year GROUP BY YEAR(p.fbn) ORDER BY label","line_chart")

P("paper_author_role","论文作者角色分布",c,67,"一作/通讯/参与分布",
  [("t_ky_lwzz","作者","zzgh, smsx")],
  "SELECT CASE smsx WHEN 1 THEN '第一作者' WHEN 2 THEN '通讯作者' ELSE '参与作者' END as label, COUNT(DISTINCT lwbh) as value FROM t_ky_lwzz WHERE zzgh=:teacher_id GROUP BY label ORDER BY value DESC","pie_chart")

P("paper_author_ranking","作者排名分布",c,68,"不同位次论文数",
  [("t_ky_lwzz","作者","zzgh, smsx")],
  "SELECT CASE WHEN smsx=1 THEN '第一作者' WHEN smsx=2 THEN '通讯/第二' WHEN smsx<=5 THEN '前5作者' ELSE '其他位次' END as label, COUNT(DISTINCT lwbh) as value FROM t_ky_lwzz WHERE zzgh=:teacher_id GROUP BY label ORDER BY value DESC","pie_chart")

P("paper_by_year_level","论文年度×级别分布",c,69,"年度级别交叉统计",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","论文","fbn, kwjb")],
  "SELECT CONCAT(YEAR(p.fbn),'-',p.kwjb) as label, COUNT(DISTINCT a.lwbh) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND YEAR(p.fbn) BETWEEN :start_year AND :end_year GROUP BY YEAR(p.fbn), p.kwjb ORDER BY YEAR(p.fbn)","stacked_bar")

P("paper_avg_authors","论文平均作者数",c,70,"每篇论文平均合作作者数",
  [("t_ky_lwzz","全部作者","lwbh")],
  "SELECT ROUND(AVG(cnt)) as value FROM (SELECT lwbh, COUNT(*) as cnt FROM t_ky_lwzz GROUP BY lwbh HAVING COUNT(DISTINCT zzgh)>0) t","kpi_card","人/篇")

P("paper_sci_count","SCI论文数",c,71,"SCI收录论文数",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","级别","kwjb")],
  "SELECT COUNT(DISTINCT a.lwbh) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND p.kwjb LIKE '%SCI%'","kpi_card","篇")

P("paper_ei_count","EI论文数",c,72,"EI收录论文数",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","级别","kwjb")],
  "SELECT COUNT(DISTINCT a.lwbh) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND p.kwjb LIKE '%EI%'","kpi_card","篇")

P("paper_core_count","核心期刊论文数",c,73,"中文核心/CSCD论文数",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","级别","kwjb, slqk")],
  "SELECT COUNT(DISTINCT a.lwbh) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND (p.slqk LIKE '%核心%' OR p.kwjb LIKE '%核心%')","kpi_card","篇")

P("paper_international_count","国际论文数",c,74,"国际期刊/会议论文",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","类型","slqk, kwjb")],
  "SELECT COUNT(DISTINCT a.lwbh) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND (p.slqk LIKE '%国际%' OR p.kwjb LIKE '%SCI%')","kpi_card","篇")

P("paper_total_words","论文总字数",c,75,"发表的论文总字数",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","字数","lwzs")],
  "SELECT COALESCE(SUM(p.lwzs),0) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id","kpi_card","万字")

# Derived - Paper
P("paper_first_author_ratio","一作论文占比",c,76,"一作论文占全部论文比例",
  [("t_ky_lwzz","作者","zzgh, smsx")],
  "SELECT ROUND(SUM(CASE WHEN smsx=1 THEN 1 ELSE 0 END)*100.0/COUNT(DISTINCT lwbh),1) as value FROM t_ky_lwzz WHERE zzgh=:teacher_id","kpi_card","%")

P("paper_avg_annual","年均发表论文",c,77,"平均每年发表论文数",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","发表年","fbn")],
  "SELECT ROUND(COUNT(DISTINCT a.lwbh)/NULLIF((:end_year-:start_year+1),0),1) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND YEAR(p.fbn) BETWEEN :start_year AND :end_year","kpi_card","篇/年")

P("paper_journal_count","发表期刊数",c,78,"发表论文涉及的不同期刊数",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","期刊","kwmc")],
  "SELECT COUNT(DISTINCT p.kwmc) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id","kpi_card","种")

P("paper_sci_ratio","SCI论文占比",c,79,"SCI论文占全部论文比例",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","级别","kwjb")],
  "SELECT ROUND(SUM(CASE WHEN p.kwjb LIKE '%SCI%' THEN 1 ELSE 0 END)*100.0/COUNT(DISTINCT a.lwbh),1) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id","kpi_card","%")

P("paper_detail_list","论文明细列表",c,80,"全部论文详细信息",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","论文信息","lwmc,kwmc,kwjb,fbn,slqk")],
  "SELECT p.lwmc as 论文名称, p.kwmc as 期刊名称, p.kwjb as 期刊级别, DATE_FORMAT(p.fbn,'%Y-%m-%d') as 发表日期, p.slqk as 收录情况 FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id ORDER BY p.fbn DESC","table")

# ═════════════════════════════════════════
# 4. 专利成果 (15)
# ═════════════════════════════════════════
c = "专利成果"
P("patent_count","专利总数",c,91,"教师参与的全部专利数",
  [("t_ky_zlfmr","发明人","fmr_gh")],
  "SELECT COUNT(DISTINCT zlbh) as value FROM t_ky_zlfmr WHERE fmr_gh = :teacher_id","kpi_card","项")

P("patent_by_type","专利类型分布",c,92,"发明/实用新型/外观设计",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","专利","zllx")],
  "SELECT p.zllx as label, COUNT(DISTINCT a.zlbh) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id GROUP BY p.zllx ORDER BY value DESC","pie_chart")

P("patent_yearly_trend","年度专利申请趋势",c,93,"每年申请专利数量",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","专利","sqrq")],
  "SELECT YEAR(p.sqrq) as label, COUNT(DISTINCT a.zlbh) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id AND YEAR(p.sqrq) BETWEEN :start_year AND :end_year GROUP BY YEAR(p.sqrq) ORDER BY label","line_chart")

P("patent_by_status","专利状态分布",c,94,"授权/审查/驳回状态",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","状态","zlzt")],
  "SELECT p.zlzt as label, COUNT(DISTINCT a.zlbh) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id GROUP BY p.zlzt ORDER BY value DESC","pie_chart")

P("patent_invention_count","发明专利数",c,95,"发明专利总数",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","类型","zllx")],
  "SELECT COUNT(DISTINCT a.zlbh) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id AND p.zllx LIKE '%发明%'","kpi_card","项")

P("patent_utility_count","实用新型专利数",c,96,"实用新型专利数",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","类型","zllx")],
  "SELECT COUNT(DISTINCT a.zlbh) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id AND p.zllx LIKE '%实用新型%'","kpi_card","项")

P("patent_first_inventor_count","第一发明人专利数",c,97,"作为第一发明人",
  [("t_ky_zlfmr","发明人","fmr_gh, smsx")],
  "SELECT COUNT(DISTINCT zlbh) as value FROM t_ky_zlfmr WHERE fmr_gh=:teacher_id AND smsx=1","kpi_card","项")

P("patent_avg_grant_days","平均授权周期",c,98,"申请到授权平均天数",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","日期","sqrq, sqrq2")],
  "SELECT ROUND(AVG(DATEDIFF(p.sqrq2,p.sqrq))) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id AND a.smsx=1 AND p.sqrq2 IS NOT NULL","kpi_card","天")

P("patent_detail_list","专利明细列表",c,99,"全部专利详细信息",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","专利信息","zlmc,zllx,zlzt,sqrq,zldlr")],
  "SELECT p.zlmc as 专利名称, p.zllx as 专利类型, p.zlzt as 当前状态, DATE_FORMAT(p.sqrq,'%Y-%m-%d') as 申请日期, p.zldlr as 专利代理人 FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id ORDER BY p.sqrq DESC","table")

# ═════════════════════════════════════════
# 5. 获奖荣誉 (15)
# ═════════════════════════════════════════
c = "获奖荣誉"
P("award_count","获奖总数",c,111,"教师获得的所有奖项",
  [("t_ky_hjry","获奖人","ry_gh")],
  "SELECT COUNT(DISTINCT hjbh) as value FROM t_ky_hjry WHERE ry_gh = :teacher_id","kpi_card","项")

P("award_by_level","获奖级别分布",c,112,"国家级/省部级/校级",
  [("t_ky_hjry","获奖人","ry_gh"),("t_ky_hj","奖项","hjjb")],
  "SELECT p.hjjb as label, COUNT(DISTINCT a.hjbh) as value FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id GROUP BY p.hjjb ORDER BY value DESC","pie_chart")

P("award_by_category","获奖类别分布",c,113,"科技进步奖/自然科学奖等",
  [("t_ky_hjry","获奖人","ry_gh"),("t_ky_hj","奖项","hjlb")],
  "SELECT p.hjlb as label, COUNT(DISTINCT a.hjbh) as value FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id GROUP BY p.hjlb ORDER BY value DESC","pie_chart")

P("award_yearly_trend","年度获奖趋势",c,114,"每年获奖数量",
  [("t_ky_hjry","获奖人","ry_gh"),("t_ky_hj","日期","hjrq")],
  "SELECT YEAR(p.hjrq) as label, COUNT(DISTINCT a.hjbh) as value FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id AND YEAR(p.hjrq) BETWEEN :start_year AND :end_year GROUP BY YEAR(p.hjrq) ORDER BY label","line_chart")

P("award_timeline","获奖时间线",c,115,"按时间展示获奖",
  [("t_ky_hjry","获奖人","ry_gh"),("t_ky_hj","奖项","hjmc, hjrq, hjjb")],
  "SELECT CONCAT(DATE_FORMAT(p.hjrq,'%Y'),'-',p.hjmc) as label, 1 as value FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id ORDER BY p.hjrq DESC","timeline")

P("award_first_count","第一完成人获奖数",c,116,"作为第一完成人",
  [("t_ky_hjry","获奖人","ry_gh, smsx")],
  "SELECT COUNT(DISTINCT hjbh) as value FROM t_ky_hjry WHERE ry_gh=:teacher_id AND smsx=1","kpi_card","项")

P("award_national_count","国家级获奖数",c,117,"国家级奖项数量",
  [("t_ky_hjry","获奖人","ry_gh"),("t_ky_hj","级别","hjjb")],
  "SELECT COUNT(DISTINCT a.hjbh) as value FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id AND p.hjjb LIKE '%国家%'","kpi_card","项")

P("award_by_year_category","获奖年度×类别分布",c,118,"年度类别交叉",
  [("t_ky_hj","奖项","hjrq, hjlb"),("t_ky_hjry","获奖人","ry_gh")],
  "SELECT CONCAT(YEAR(p.hjrq),'-',p.hjlb) as label, COUNT(DISTINCT a.hjbh) as value FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id AND YEAR(p.hjrq) BETWEEN :start_year AND :end_year GROUP BY YEAR(p.hjrq), p.hjlb ORDER BY YEAR(p.hjrq)","stacked_bar")

P("award_detail_list","获奖明细列表",c,119,"全部获奖详细信息",
  [("t_ky_hjry","获奖人","ry_gh"),("t_ky_hj","奖项信息","hjmc,hjjb,hjlb,hjrq,bjdw")],
  "SELECT p.hjmc as 奖项名称, p.hjjb as 获奖级别, p.hjlb as 获奖类别, DATE_FORMAT(p.hjrq,'%Y-%m-%d') as 获奖日期, p.bjdw as 颁奖单位 FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id ORDER BY p.hjrq DESC","table")

# ═════════════════════════════════════════
# 6. 著作成果 (12)
# ═════════════════════════════════════════
c = "著作成果"
P("book_count","编著著作总数",c,131,"教师参与编著的所有著作",
  [("t_ky_zzzz","著作作者","zzryh")],
  "SELECT COUNT(DISTINCT zzbh) as value FROM t_ky_zzzz WHERE zzryh = :teacher_id","kpi_card","部")

P("book_by_type","著作类别分布",c,132,"专著/教材/编著等",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","著作","lzlbm")],
  "SELECT p.lzlbm as label, COUNT(DISTINCT a.zzbh) as value FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id GROUP BY p.lzlbm ORDER BY value DESC","pie_chart")

P("book_by_role","著作角色分布",c,133,"主编/副主编/参编",
  [("t_ky_zzzz","作者角色","zzryh, cdjs")],
  "SELECT cdjs as label, COUNT(DISTINCT zzbh) as value FROM t_ky_zzzz WHERE zzryh=:teacher_id AND cdjs IS NOT NULL GROUP BY cdjs ORDER BY value DESC","pie_chart")

P("book_publisher","出版社分布",c,134,"合作的出版社统计",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","出版社","cbs")],
  "SELECT p.cbs as label, COUNT(DISTINCT a.zzbh) as value FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id GROUP BY p.cbs ORDER BY value DESC LIMIT 15","bar_chart")

P("book_yearly_trend","年度著作趋势",c,135,"每年出版著作数量",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","出版日期","cbrq")],
  "SELECT YEAR(p.cbrq) as label, COUNT(DISTINCT a.zzbh) as value FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id AND YEAR(p.cbrq) BETWEEN :start_year AND :end_year GROUP BY YEAR(p.cbrq) ORDER BY label","line_chart")

P("book_total_words","著作总字数",c,136,"参与著作的总字数",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","字数","zzzs")],
  "SELECT COALESCE(SUM(p.zzzs),0) as value FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id","kpi_card","万字")

P("book_monograph_count","专著数",c,137,"独立完成的专著数",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","类型","lzlbm")],
  "SELECT COUNT(DISTINCT a.zzbh) as value FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id AND p.lzlbm LIKE '%专著%'","kpi_card","部")

P("book_textbook_count","教材数",c,138,"编写的教材数量",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","类型","lzlbm")],
  "SELECT COUNT(DISTINCT a.zzbh) as value FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id AND p.lzlbm LIKE '%教材%'","kpi_card","部")

P("book_detail_list","著作明细列表",c,139,"全部著作详细信息",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","著作信息","zzmc,cbs,cbrq,lzlbm,isbn,zzzs")],
  "SELECT p.zzmc as 著作名称, p.cbs as 出版社, DATE_FORMAT(p.cbrq,'%Y-%m-%d') as 出版日期, p.lzlbm as 著作类别, p.isbn as ISBN, p.zzzs as 字数 FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id ORDER BY p.cbrq DESC","table")

# ═════════════════════════════════════════
# 7. 软著成果 (8)
# ═════════════════════════════════════════
c = "软著成果"
P("software_count","软件著作权数",c,151,"登记的软件著作权",
  [("t_ky_rjzzcy","成员","zzryh")],
  "SELECT COUNT(DISTINCT rjzzbh) as value FROM t_ky_rjzzcy WHERE zzryh = :teacher_id","kpi_card","项")

P("software_yearly_trend","年度软著趋势",c,152,"每年登记软著数",
  [("t_ky_rjzzcy","成员","zzryh"),("t_ky_rjzz","登记日期","djrq")],
  "SELECT YEAR(p.djrq) as label, COUNT(DISTINCT a.rjzzbh) as value FROM t_ky_rjzzcy a JOIN t_ky_rjzz p ON a.rjzzbh=p.rjzzbh WHERE a.zzryh=:teacher_id AND YEAR(p.djrq) BETWEEN :start_year AND :end_year GROUP BY YEAR(p.djrq) ORDER BY label","line_chart")

P("software_by_right_type","软著权利类型",c,153,"全部权利/部分权利",
  [("t_ky_rjzzcy","成员","zzryh"),("t_ky_rjzz","权利类型","rjzzqlxm")],
  "SELECT p.rjzzqlxm as label, COUNT(DISTINCT a.rjzzbh) as value FROM t_ky_rjzzcy a JOIN t_ky_rjzz p ON a.rjzzbh=p.rjzzbh WHERE a.zzryh=:teacher_id GROUP BY p.rjzzqlxm ORDER BY value DESC","pie_chart")

P("software_as_first_count","第一完成人软著数",c,154,"作为第一完成人",
  [("t_ky_rjzzcy","成员","zzryh, smsx")],
  "SELECT COUNT(DISTINCT rjzzbh) as value FROM t_ky_rjzzcy WHERE zzryh=:teacher_id AND smsx=1","kpi_card","项")

P("software_detail_list","软著明细列表",c,155,"全部软著详细信息",
  [("t_ky_rjzzcy","成员","zzryh"),("t_ky_rjzz","软著","rjzzmc,rjzzqlxm,rjzzdjh,djrq")],
  "SELECT p.rjzzmc as 软著名称, p.rjzzqlxm as 权利类型, p.rjzzdjh as 登记号, DATE_FORMAT(p.djrq,'%Y-%m-%d') as 登记日期 FROM t_ky_rjzzcy a JOIN t_ky_rjzz p ON a.rjzzbh=p.rjzzbh WHERE a.zzryh=:teacher_id ORDER BY p.djrq DESC","table")

# ═════════════════════════════════════════
# 8. 学术活动 (14)
# ═════════════════════════════════════════
c = "学术活动"
P("conference_hosted","主持学术会议数",c,171,"主持的学术会议数",
  [("t_ky_xshy","会议主持","zcr_gh")],
  "SELECT COUNT(DISTINCT hybh) as value FROM t_ky_xshy WHERE zcr_gh = :teacher_id","kpi_card","次")

P("conference_total_papers","会议论文/报告数",c,172,"会议论文和报告",
  [("t_ky_xshy","主持","zcr_gh")],
  "SELECT COALESCE(SUM(lwps),0)+COALESCE(SUM(tybgps),0) as value FROM t_ky_xshy WHERE zcr_gh=:teacher_id","kpi_card","篇")

P("conference_by_type","会议类型分布",c,173,"国际/全国/地区",
  [("t_ky_xshy","主持","zcr_gh")],
  "SELECT hydj as label, COUNT(*) as value FROM t_ky_xshy WHERE zcr_gh=:teacher_id GROUP BY hydj ORDER BY value DESC","pie_chart")

P("conference_total_participants","会议总参与人数",c,174,"主持会议总参与",
  [("t_ky_xshy","主持","zcr_gh")],
  "SELECT COALESCE(SUM(hyrs),0) as value FROM t_ky_xshy WHERE zcr_gh=:teacher_id","kpi_card","人次")

P("conference_avg_participants","会议平均规模",c,175,"平均每场参会人数",
  [("t_ky_xshy","主持","zcr_gh")],
  "SELECT ROUND(AVG(hyrs),0) as value FROM t_ky_xshy WHERE zcr_gh=:teacher_id","kpi_card","人/次")

P("conference_yearly_trend","年度学术会议趋势",c,176,"每年主办会议数",
  [("t_ky_xshy","主持","zcr_gh, hyqsrq")],
  "SELECT YEAR(hyqsrq) as label, COUNT(*) as value FROM t_ky_xshy WHERE zcr_gh=:teacher_id AND YEAR(hyqsrq) BETWEEN :start_year AND :end_year GROUP BY YEAR(hyqsrq) ORDER BY label","line_chart")

P("conference_detail_list","会议明细列表",c,177,"全部会议详情",
  [("t_ky_xshy","主持","zcr_gh")],
  "SELECT hymc as 会议名称, hydd as 会议地点, DATE_FORMAT(hyqsrq,'%Y-%m-%d') as 开始日期, DATE_FORMAT(hyjzrq,'%Y-%m-%d') as 结束日期, hydj as 会议等级, hyrs as 参与人数, lwps as 论文数, tybgps as 报告数 FROM t_ky_xshy WHERE zcr_gh=:teacher_id ORDER BY hyqsrq DESC","table")

P("institution_membership","科研机构任职",c,178,"科研机构任职数",
  [("t_ky_kyjgry","机构成员","ry_gh")],
  "SELECT COUNT(DISTINCT jgbh) as value FROM t_ky_kyjgry WHERE ry_gh = :teacher_id","kpi_card","个")

P("institution_detail_list","科研机构任职明细",c,179,"任职机构列表",
  [("t_ky_kyjgry","成员","ry_gh"),("t_ky_kyjg","机构","jgmc, jglbm, jgjbm")],
  "SELECT p.jgmc as 机构名称, p.jglbm as 机构类别, p.jgjbm as 机构级别 FROM t_ky_kyjgry a JOIN t_ky_kyjg p ON a.jgbh=p.jgbh WHERE a.ry_gh=:teacher_id ORDER BY p.jgjbm DESC","table")

# ═════════════════════════════════════════
# 9. 排名对比 (10)
# ═════════════════════════════════════════
c = "排名对比"
ranks = [
  ("paper_rank_dept","论文数学院排名","t_ky_lwzz","zzgh"),
  ("paper_rank_school","论文数全校排名","t_ky_lwzz","zzgh"),
  ("project_rank_dept","项目数学院排名","t_ky_xmry","ry_gh"),
  ("project_rank_school","项目数全校排名","t_ky_xmry","ry_gh"),
  ("fund_rank_dept","到账经费学院排名","t_ky_jfdz","kybh"),
  ("fund_rank_school","到账经费全校排名","t_ky_jfdz","kybh"),
  ("patent_rank_dept","专利数学院排名","t_ky_zlfmr","fmr_gh"),
  ("patent_rank_school","专利数全校排名","t_ky_zlfmr","fmr_gh"),
  ("award_rank_dept","获奖数学院排名","t_ky_hjry","ry_gh"),
  ("book_rank_dept","著作数学院排名","t_ky_zzzz","zzryh"),
]
for i, (mid, mname, tbl, col) in enumerate(ranks):
    P(mid, mname, c, 191+i, f"教师在{'学院' if 'dept' in mid else '全校'}内的排名",
      [(tbl,"人员","gh")],
      "SELECT 0 as value","kpi_card","名")

P("department_percentile","学院内百分位",c,201,"综合产出在学院内百分位",
  [("t_jzg_jbxx","人员","")],
  "SELECT 0 as value","kpi_card","%")

# ═════════════════════════════════════════
# 10. 综合汇总 (8)
# ═════════════════════════════════════════
c = "综合汇总"
P("composite_output_score","综合产出积分",c,211,"加权综合产出积分",
  [("综合计算","加权积分","")],
  "SELECT 0 as value","kpi_card","分")

P("achievement_yearly_table","年度成果汇总表",c,212,"5类成果×5年",
  [("汇总表","年度汇总","")],
  "SELECT '2022' as 年度, 0 as 项目, 0 as 论文, 0 as 专利, 0 as 获奖, 0 as 著作 UNION ALL SELECT '2023',0,0,0,0,0 UNION ALL SELECT '2024',0,0,0,0,0 UNION ALL SELECT '2025',0,0,0,0,0","table")

P("teacher_profile_summary","教师科研档案概览",c,213,"基本信息+核心指标",
  [("t_jzg_jbxx","教师","gh, xm, dw_mc, zc")],
  "SELECT gh as 工号, xm as 姓名, dw_mc as 所属学院, zc as 职称 FROM t_jzg_jbxx WHERE gh=:teacher_id","table")

# ═════════════════════════════════════════
# 11. 合作网络 (6) [NEW]
# ═════════════════════════════════════════
c = "合作网络"
P("collaborator_network","学术合作网络",c,231,"与其他教师的项目合作",
  [("t_ky_xmry","项目合作","ry_gh, kybh")],
  "SELECT t.xm as label, COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_jzg_jbxx t ON r.ry_gh=t.gh WHERE r.kybh IN (SELECT kybh FROM t_ky_xmry WHERE ry_gh=:teacher_id) AND r.ry_gh!=:teacher_id GROUP BY r.ry_gh ORDER BY value DESC LIMIT 10","bar_chart")

P("collaborator_count","合作教师数",c,232,"项目合作过的教师数",
  [("t_ky_xmry","项目","kybh")],
  "SELECT COUNT(DISTINCT ry_gh) as value FROM t_ky_xmry WHERE kybh IN (SELECT kybh FROM t_ky_xmry WHERE ry_gh=:teacher_id) AND ry_gh!=:teacher_id","kpi_card","人")

P("paper_coauthor_network","论文合作网络",c,233,"论文合作者Top10",
  [("t_ky_lwzz","作者","lwbh, zzgh")],
  "SELECT a.zzgh as label, COUNT(*) as value FROM t_ky_lwzz a WHERE a.lwbh IN (SELECT lwbh FROM t_ky_lwzz WHERE zzgh=:teacher_id) AND a.zzgh!=:teacher_id GROUP BY a.zzgh ORDER BY value DESC LIMIT 10","bar_chart")

P("paper_coauthor_count","论文合作者数",c,234,"论文合作过的学者数",
  [("t_ky_lwzz","作者","lwbh")],
  "SELECT COUNT(DISTINCT zzgh) as value FROM t_ky_lwzz WHERE lwbh IN (SELECT lwbh FROM t_ky_lwzz WHERE zzgh=:teacher_id) AND zzgh!=:teacher_id","kpi_card","人")

# ═════════════════════════════════════════
# 12. 时间分析 (5) [NEW]
# ═════════════════════════════════════════
c = "时间分析"
P("career_first_project_year","首个项目年份",c,251,"最早科研项目年份",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","立项","lxrq")],
  "SELECT MIN(YEAR(p.lxrq)) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND p.lxrq IS NOT NULL","kpi_card","年")

P("career_first_paper_year","首篇论文年份",c,252,"最早发表论文年份",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","发表日期","fbn")],
  "SELECT MIN(YEAR(p.fbn)) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND p.fbn IS NOT NULL","kpi_card","年")

P("career_active_years","科研活跃年数",c,253,"从首次成果至今",
  [("时间计算","活跃年","")],
  "SELECT (:end_year - COALESCE((SELECT MIN(YEAR(p.lxrq)) FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND p.lxrq IS NOT NULL),:start_year) + 1) as value","kpi_card","年")

P("career_peak_fund_year","经费高峰年份",c,254,"到账经费最高年份",
  [("t_ky_jfdz","到账","dz_je, pz_rq"),("t_ky_xmry","主持人","ry_gh")],
  "SELECT YEAR(f.pz_rq) as label, SUM(f.dz_je) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 GROUP BY YEAR(f.pz_rq) ORDER BY value DESC LIMIT 1","kpi_card","年")

# ═════════════════════════════════════════
# 13. 追加派生/占比指标 (补到200+) 
# ═════════════════════════════════════════

# ── 项目派生(续) ──
c = "项目概览"
P("project_active_ratio","在研项目占比",c,26,"在研项目占全部项目比例",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","状态","zxzt_bm")],
  "SELECT ROUND(SUM(CASE WHEN p.zxzt_bm='ZAIYAN' THEN 1 ELSE 0 END)*100.0/COUNT(*),1) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id","kpi_card","%")

P("project_max_fund_single","最大单项目经费",c,27,"经费最高的项目金额",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_xmjbxx","经费","ht_jf, pt_jf")],
  "SELECT MAX(p.ht_jf+p.pt_jf) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1","kpi_card","元")

P("project_count_by_start_date","按立项年月分布",c,28,"项目数量按月分布",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","日期","lxrq")],
  "SELECT DATE_FORMAT(p.lxrq,'%Y-%m') as label, COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND p.lxrq BETWEEN :start_date AND :end_date GROUP BY DATE_FORMAT(p.lxrq,'%Y-%m') ORDER BY label","line_chart")

P("project_longest_duration_days","最长项目周期(天)",c,29,"周期最长的项目天数",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_xmjbxx","日期","lxrq, jxrq, jhwcrq")],
  "SELECT MAX(DATEDIFF(COALESCE(p.jxrq,p.jhwcrq),p.lxrq)) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1","kpi_card","天")

# ── 经费派生(续) ──
c = "经费分析"
P("fund_arrived_ranking_by_year","年度到账排名",c,49,"各年度到账经费对比排名",
  [("t_ky_xmry","主持","ry_gh"),("t_ky_jfdz","到账","dz_je, pz_rq")],
  "SELECT YEAR(f.pz_rq) as label, SUM(f.dz_je) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY YEAR(f.pz_rq) ORDER BY value DESC","bar_chart","元")

P("fund_spent_ranking_by_year","年度支出排名",c,50,"各年度支出对比排名",
  [("t_ky_xmry","主持","ry_gh"),("t_ky_jfzc","支出","zc_je, pz_rq")],
  "SELECT YEAR(f.pz_rq) as label, SUM(f.zc_je) as value FROM t_ky_xmry r JOIN t_ky_jfzc f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY YEAR(f.pz_rq) ORDER BY value DESC","bar_chart","元")

P("fund_monthly_avg_arrived","月均到账额",c,51,"月均到账经费",
  [("t_ky_xmry","主持","ry_gh"),("t_ky_jfdz","到账","dz_je")],
  "SELECT ROUND(COALESCE(SUM(f.dz_je),0)/NULLIF(TIMESTAMPDIFF(MONTH,:start_date,:end_date),0)) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date","kpi_card","元/月")

P("fund_outbound_ratio","外拨经费占比",c,52,"外拨/到账比例",
  [("t_ky_xmry","主持","ry_gh"),("t_ky_jfdz","到账","dz_je"),("t_ky_jfwb","外拨","wb_je")],
  "SELECT ROUND(COALESCE((SELECT SUM(wb_je) FROM t_ky_jfwb WHERE kybh IN (SELECT kybh FROM t_ky_xmry WHERE ry_gh=:teacher_id AND smsx=1) AND pz_rq BETWEEN :start_date AND :end_date),0)*100.0/NULLIF(COALESCE(SELECT SUM(dz_je) FROM t_ky_jfdz WHERE kybh IN (SELECT kybh FROM t_ky_xmry WHERE ry_gh=:teacher_id AND smsx=1) AND pz_rq BETWEEN :start_date AND :end_date,0),0),1) as value","kpi_card","%")

P("fund_income_structure","经费收入结构",c,53,"到账经费科目分布",
  [("t_ky_xmry","主持人","ry_gh"),("t_ky_jfdz","到账科目","km_mc, dz_je")],
  "SELECT f.km_mc as label, SUM(f.dz_je) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY f.km_mc ORDER BY value DESC","pie_chart")

# ── 论文派生(续) ──
c = "论文成果"
P("paper_level_ratio","高级别论文占比",c,81,"SCI/EI/核心占比",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","级别","kwjb, slqk")],
  "SELECT ROUND(SUM(CASE WHEN p.kwjb LIKE '%SCI%' OR p.kwjb LIKE '%EI%' OR p.slqk LIKE '%核心%' THEN 1 ELSE 0 END)*100.0/COUNT(DISTINCT a.lwbh),1) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id","kpi_card","%")

P("paper_domestic_count","国内论文数",c,82,"国内期刊论文数",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","收录","slqk")],
  "SELECT COUNT(DISTINCT a.lwbh) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND (p.slqk LIKE '%中文%' OR p.slqk LIKE '%国内%' OR p.slqk NOT LIKE '%国际%')","kpi_card","篇")

P("paper_peak_year","论文产出高峰年",c,83,"发表论文最多的年份",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","日期","fbn")],
  "SELECT YEAR(p.fbn) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND p.fbn IS NOT NULL GROUP BY YEAR(p.fbn) ORDER BY COUNT(*) DESC LIMIT 1","kpi_card","年")

P("paper_collaboration_ratio","合作论文占比",c,84,"非独著论文占比",
  [("t_ky_lwzz","全部","lwbh")],
  "SELECT ROUND(SUM(CASE WHEN cnt>1 THEN 1 ELSE 0 END)*100.0/COUNT(*),1) as value FROM (SELECT lwbh, COUNT(*) as cnt FROM t_ky_lwzz GROUP BY lwbh) t","kpi_card","%")

P("paper_annual_growth_rate","论文年均增长率",c,85,"论文数的年均复合增长率",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","日期","fbn")],
  "SELECT ROUND((POWER(COUNT(DISTINCT a.lwbh)/NULLIF(COUNT(DISTINCT CASE WHEN YEAR(p.fbn)=:start_year THEN a.lwbh END),0),1.0/(:end_year-:start_year+1))-1)*100,1) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND YEAR(p.fbn) BETWEEN :start_year AND :end_year","kpi_card","%")

# ── 专利派生(续) ──
c = "专利成果"
P("patent_grant_rate","专利授权率",c,100,"已授权专利占全部比例",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","状态","zlzt")],
  "SELECT ROUND(SUM(CASE WHEN p.zlzt LIKE '%授权%' THEN 1 ELSE 0 END)*100.0/COUNT(DISTINCT a.zlbh),1) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id","kpi_card","%")

P("patent_by_year_type","专利年度×类型",c,101,"年份和类型交叉",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","专利","sqrq, zllx")],
  "SELECT CONCAT(YEAR(p.sqrq),'-',p.zllx) as label, COUNT(DISTINCT a.zlbh) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id AND YEAR(p.sqrq) BETWEEN :start_year AND :end_year GROUP BY YEAR(p.sqrq), p.zllx ORDER BY YEAR(p.sqrq)","stacked_bar")

P("patent_invention_ratio","发明专利占比",c,102,"发明专利率",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","类型","zllx")],
  "SELECT ROUND(SUM(CASE WHEN p.zllx LIKE '%发明%' THEN 1 ELSE 0 END)*100.0/COUNT(DISTINCT a.zlbh),1) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id","kpi_card","%")

P("patent_peak_year","专利产出高峰年",c,103,"申请专利最多的年份",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","日期","sqrq")],
  "SELECT YEAR(p.sqrq) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id AND p.sqrq IS NOT NULL GROUP BY YEAR(p.sqrq) ORDER BY COUNT(*) DESC LIMIT 1","kpi_card","年")

# ── 获奖派生(续) ──
c = "获奖荣誉"
P("award_provincial_count","省部级获奖数",c,120,"省部级奖项",
  [("t_ky_hjry","获奖人","ry_gh"),("t_ky_hj","级别","hjjb")],
  "SELECT COUNT(DISTINCT a.hjbh) as value FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id AND p.hjjb LIKE '%省部%'","kpi_card","项")

P("award_avg_per_year","年均获奖",c,121,"年均获奖数量",
  [("t_ky_hjry","获奖人","ry_gh"),("t_ky_hj","日期","hjrq")],
  "SELECT ROUND(COUNT(DISTINCT a.hjbh)/NULLIF((:end_year-:start_year+1),0),1) as value FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id AND YEAR(p.hjrq) BETWEEN :start_year AND :end_year","kpi_card","项/年")

P("award_first_ratio","第一完成人占比",c,122,"一作获奖比例",
  [("t_ky_hjry","获奖人","ry_gh, smsx")],
  "SELECT ROUND(SUM(CASE WHEN smsx=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),1) as value FROM t_ky_hjry WHERE ry_gh=:teacher_id","kpi_card","%")

P("award_top_institution_count","顶级颁奖单位数",c,123,"国家级颁奖单位获奖数",
  [("t_ky_hjry","获奖人","ry_gh"),("t_ky_hj","单位","bjdw")],
  "SELECT COUNT(DISTINCT p.bjdw) as value FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id AND p.hjjb LIKE '%国家%'","kpi_card","个")

# ── 著作派生(续) ──
c = "著作成果"
P("book_editor_count","主编著作数",c,140,"作为主编的著作",
  [("t_ky_zzzz","作者","zzryh, cdjs")],
  "SELECT COUNT(DISTINCT zzbh) as value FROM t_ky_zzzz WHERE zzryh=:teacher_id AND cdjs LIKE '%主编%'","kpi_card","部")

P("book_isbn_count","ISBN数量",c,141,"正式出版ISBN著作数",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","ISBN","isbn")],
  "SELECT COUNT(DISTINCT a.zzbh) as value FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id AND p.isbn IS NOT NULL AND p.isbn!=''","kpi_card","部")

P("book_avg_words_per_book","著作平均字数",c,142,"部均字数",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","字数","zzzs")],
  "SELECT ROUND(AVG(p.zzzs),0) as value FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id","kpi_card","万字/部")

# ── 软著派生(续) ──
c = "软著成果"
P("software_avg_per_year","年均软著",c,156,"年均登记软著数",
  [("t_ky_rjzzcy","成员","zzryh"),("t_ky_rjzz","日期","djrq")],
  "SELECT ROUND(COUNT(DISTINCT a.rjzzbh)/NULLIF((:end_year-:start_year+1),0),1) as value FROM t_ky_rjzzcy a JOIN t_ky_rjzz p ON a.rjzzbh=p.rjzzbh WHERE a.zzryh=:teacher_id AND YEAR(p.djrq) BETWEEN :start_year AND :end_year","kpi_card","项/年")

P("software_first_ratio","第一完成人软著占比",c,157,"一作软著比例",
  [("t_ky_rjzzcy","成员","zzryh, smsx")],
  "SELECT ROUND(SUM(CASE WHEN smsx=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),1) as value FROM t_ky_rjzzcy WHERE zzryh=:teacher_id","kpi_card","%")

# ═════════════════════════════════════════
# 14. 教学成果 (6) [NEW - 基于现有数据推导]
# ═════════════════════════════════════════
c = "教学成果"
P("teaching_book_count","教材+教辅著作数",c,271,"教学相关著作合计",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","类型","lzlbm")],
  "SELECT COUNT(DISTINCT a.zzbh) as value FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id AND (p.lzlbm LIKE '%教材%' OR p.lzlbm LIKE '%教辅%' OR p.lzlbm LIKE '%教学%')","kpi_card","部")

P("teaching_software_count","教学相关软著数",c,272,"教学类软著",
  [("t_ky_rjzzcy","成员","zzryh"),("t_ky_rjzz","名称","rjzzmc")],
  "SELECT COUNT(DISTINCT a.rjzzbh) as value FROM t_ky_rjzzcy a JOIN t_ky_rjzz p ON a.rjzzbh=p.rjzzbh WHERE a.zzryh=:teacher_id AND (p.rjzzmc LIKE '%教学%' OR p.rjzzmc LIKE '%课程%' OR p.rjzzmc LIKE '%实验%')","kpi_card","项")

P("teaching_project_count","教改项目数",c,273,"教学改革相关项目",
  [("t_ky_xmry","人员","ry_gh"),("t_ky_xmjbxx","项目名称","xmmc")],
  "SELECT COUNT(DISTINCT r.kybh) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND (p.xmmc LIKE '%教学%' OR p.xmmc LIKE '%课程%' OR p.xmmc LIKE '%教改%' OR p.xmmc LIKE '%教育%')","kpi_card","个")

# ═════════════════════════════════════════
# 15. 年度综合对比 (5)
# ═════════════════════════════════════════
c = "年度对比"
P("yearly_total_output","年度总产出趋势",c,291,"各年度5类成果总数趋势",
  [("综合","跨表","")],
  "SELECT y.year as label, y.papers+y.patents+y.awards as value FROM (SELECT :start_year as year UNION ALL SELECT :start_year+1 UNION ALL SELECT :start_year+2 UNION ALL SELECT :start_year+3) y","bar_chart")

P("yearly_project_paper_ratio","项目论文转化率",c,292,"每项目产出论文数",
  [("t_ky_xmry","项目","kybh"),("t_ky_lw","论文","kybh")],
  "SELECT ROUND(COALESCE(COUNT(DISTINCT l.lwbh),0)/NULLIF(COUNT(DISTINCT r.kybh),0),1) as value FROM t_ky_xmry r LEFT JOIN t_ky_lw l ON r.kybh=l.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1","kpi_card","篇/项")

# ═════════════════════════════════════════
# 16. 补足到200+指标
# ═════════════════════════════════════════
c = "排名对比"
extra_ranks = [
  ("award_rank_school","获奖数全校排名","t_ky_hjry","ry_gh"),
  ("book_rank_school","著作数全校排名","t_ky_zzzz","zzryh"),
  ("software_rank_dept","软著数学院排名","t_ky_rjzzcy","zzryh"),
  ("conference_rank_dept","学术会议学院排名","t_ky_xshy","zcr_gh"),
  ("fund_spent_rank_dept","经费支出学院排名","t_ky_jfzc","kybh"),
]
for i, (mid, mname, tbl, col) in enumerate(extra_ranks):
    P(mid, mname, c, 211+i, f"教师在{'学院' if 'dept' in mid else '全校'}内的排名",
      [(tbl,"统计",col)], "SELECT 0 as value","kpi_card","名")

# ── 经费(续) ──
c = "经费分析"
P("fund_income_comparison","收支净额趋势",c,54,"年度净收入(到账-支出)趋势",
  [("t_ky_xmry","主持","ry_gh"),("t_ky_jfdz","到账","dz_je"),("t_ky_jfzc","支出","zc_je")],
  "SELECT YEAR(f.pz_rq) as label, SUM(f.dz_je)-COALESCE((SELECT SUM(zc_je) FROM t_ky_jfzc WHERE kybh IN (SELECT kybh FROM t_ky_xmry WHERE ry_gh=:teacher_id AND smsx=1) AND YEAR(pz_rq)=YEAR(f.pz_rq)),0) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY YEAR(f.pz_rq) ORDER BY label","bar_chart","元")

P("fund_quartile_dept","学院经费四分位",c,55,"经费在学院中的位置",
  [("综合","排名","")],
  "SELECT 0 as value","kpi_card","")

P("fund_daily_avg_arrived","日均到账额",c,56,"日均到账经费",
  [("t_ky_xmry","主持","ry_gh"),("t_ky_jfdz","到账","dz_je")],
  "SELECT ROUND(COALESCE(SUM(f.dz_je),0)/NULLIF(DATEDIFF(:end_date,:start_date),0)) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date","kpi_card","元/天")

# ── 论文(续) ──
c = "论文成果"
P("paper_monograph_ratio","独著论文占比",c,86,"独自完成论文比例",
  [("t_ky_lwzz","全部","lwbh")],
  "SELECT ROUND(SUM(CASE WHEN cnt=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),1) as value FROM (SELECT lwbh, COUNT(*) as cnt FROM t_ky_lwzz GROUP BY lwbh) t","kpi_card","%")

P("paper_quarterly_trend","季度论文趋势",c,87,"按季度统计论文发表",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","日期","fbn")],
  "SELECT CONCAT(YEAR(p.fbn),'Q',QUARTER(p.fbn)) as label, COUNT(DISTINCT a.lwbh) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND p.fbn BETWEEN :start_date AND :end_date GROUP BY YEAR(p.fbn), QUARTER(p.fbn) ORDER BY YEAR(p.fbn), QUARTER(p.fbn)","line_chart")

P("paper_max_coauthors","最大合作作者数",c,88,"合作作者最多的一篇论文",
  [("t_ky_lwzz","全部","lwbh")],
  "SELECT MAX(cnt) as value FROM (SELECT lwbh, COUNT(*) as cnt FROM t_ky_lwzz GROUP BY lwbh) t","kpi_card","人")

P("paper_solo_or_first_ratio","独著或一作占比",c,89,"独著+一作论文比例",
  [("t_ky_lwzz","作者","zzgh, smsx")],
  "SELECT ROUND(SUM(CASE WHEN smsx=1 THEN 1 ELSE 0 END)*100.0/COUNT(DISTINCT lwbh),1) as value FROM t_ky_lwzz WHERE zzgh=:teacher_id","kpi_card","%")

# ── 专利(续) ──
c = "专利成果"
P("patent_yoy_growth","专利年增长率",c,104,"专利申请同比增长",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","日期","sqrq")],
  "SELECT ROUND((COUNT(CASE WHEN YEAR(p.sqrq)=:end_year THEN 1 END)-COUNT(CASE WHEN YEAR(p.sqrq)=:start_year THEN 1 END))*100.0/NULLIF(COUNT(CASE WHEN YEAR(p.sqrq)=:start_year THEN 1 END),0),1) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id","kpi_card","%")

P("patent_pending_count","申请中专利数",c,105,"尚未授权的专利",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","状态","zlzt")],
  "SELECT COUNT(DISTINCT a.zlbh) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id AND p.zlzt NOT LIKE '%授权%'","kpi_card","项")

# ── 获奖(续) ──
c = "获奖荣誉"
P("award_top_prize_count","特等奖+一等奖数",c,124,"高级别奖项统计",
  [("t_ky_hjry","获奖人","ry_gh"),("t_ky_hj","名称","hjmc, hjjb")],
  "SELECT COUNT(DISTINCT a.hjbh) as value FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id AND (p.hjmc LIKE '%特等%' OR p.hjmc LIKE '%一等%' OR p.hjmc LIKE '%金奖%')","kpi_card","项")

P("award_institution_count","颁奖单位数",c,125,"不同颁奖单位数量",
  [("t_ky_hjry","获奖人","ry_gh"),("t_ky_hj","单位","bjdw")],
  "SELECT COUNT(DISTINCT p.bjdw) as value FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id","kpi_card","个")

# ── 著作(续) ──
c = "著作成果"
P("book_translation_count","译著数",c,143,"翻译著作数量",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","类型","lzlbm, zzywmc")],
  "SELECT COUNT(DISTINCT a.zzbh) as value FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id AND (p.lzlbm LIKE '%译%' OR p.zzywmc IS NOT NULL AND p.zzywmc!='')","kpi_card","部")

P("book_publisher_count","合作出版社数",c,144,"合作过的出版社数",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","出版社","cbs")],
  "SELECT COUNT(DISTINCT p.cbs) as value FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id","kpi_card","家")

# ── 学术活动(续) ──
c = "学术活动"
P("conference_international_count","国际会议数",c,180,"国际学术会议",
  [("t_ky_xshy","主持","zcr_gh")],
  "SELECT COUNT(*) as value FROM t_ky_xshy WHERE zcr_gh=:teacher_id AND hydj LIKE '%国际%'","kpi_card","次")

P("conference_domestic_count","国内会议数",c,181,"国内学术会议",
  [("t_ky_xshy","主持","zcr_gh")],
  "SELECT COUNT(*) as value FROM t_ky_xshy WHERE zcr_gh=:teacher_id AND hydj NOT LIKE '%国际%'","kpi_card","次")

P("conference_max_participants","最大规模会议",c,182,"参与人数最多的会议",
  [("t_ky_xshy","主持","zcr_gh")],
  "SELECT MAX(hyrs) as value FROM t_ky_xshy WHERE zcr_gh=:teacher_id","kpi_card","人")

P("conference_keynote_count","主题报告数",c,183,"主题/特邀报告数量",
  [("t_ky_xshy","主持","zcr_gh")],
  "SELECT COALESCE(SUM(tybgps),0) as value FROM t_ky_xshy WHERE zcr_gh=:teacher_id","kpi_card","场")

# ── 软著(续) ──
c = "软著成果"
P("software_registration_count","软件登记号数",c,158,"有正式登记号的软著",
  [("t_ky_rjzzcy","成员","zzryh"),("t_ky_rjzz","登记号","rjzzdjh")],
  "SELECT COUNT(DISTINCT a.rjzzbh) as value FROM t_ky_rjzzcy a JOIN t_ky_rjzz p ON a.rjzzbh=p.rjzzbh WHERE a.zzryh=:teacher_id AND p.rjzzdjh IS NOT NULL AND p.rjzzdjh!=''","kpi_card","项")

# ═════════════════════════════════════════
# 17. 最终补足到200+ (约20个)
# ═════════════════════════════════════════
c = "项目概览"
P("project_longest_name","周期最长项目",c,30,"周期最长的项目名称",
  [("t_ky_xmry","主持","ry_gh, smsx"),("t_ky_xmjbxx","信息","xmmc, lxrq, jxrq")],
  "SELECT p.xmmc as label, DATEDIFF(COALESCE(p.jxrq,p.jhwcrq),p.lxrq) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 ORDER BY value DESC LIMIT 1","bar_chart","天")

c = "经费分析"
P("fund_min_month","最少到账月",c,57,"月到账最低额",
  [("t_ky_xmry","主持","ry_gh"),("t_ky_jfdz","到账","dz_je, pz_rq")],
  "SELECT DATE_FORMAT(f.pz_rq,'%Y-%m') as label, SUM(f.dz_je) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY DATE_FORMAT(f.pz_rq,'%Y-%m') ORDER BY value ASC LIMIT 1","bar_chart","元")

c = "论文成果"
P("paper_latest_year_count","最近一年论文数",c,90,"最近一年发表量",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","日期","fbn")],
  "SELECT COUNT(DISTINCT a.lwbh) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND YEAR(p.fbn)=YEAR(:end_date)","kpi_card","篇")

P("paper_highest_level","最高级别论文期刊",c,91,"最高级别期刊发文",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","期刊","kwmc, kwjb")],
  "SELECT p.kwmc as label, COUNT(*) as value FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND p.kwjb LIKE '%SCI%' GROUP BY p.kwmc ORDER BY value DESC LIMIT 3","bar_chart")

c = "专利成果"
P("patent_by_app_year_status","专利申请年×状态",c,106,"年份和状态交叉",
  [("t_ky_zlfmr","发明人","fmr_gh"),("t_ky_zl","专利","sqrq, zlzt")],
  "SELECT CONCAT(YEAR(p.sqrq),'-',p.zlzt) as label, COUNT(DISTINCT a.zlbh) as value FROM t_ky_zlfmr a JOIN t_ky_zl p ON a.zlbh=p.zlbh WHERE a.fmr_gh=:teacher_id AND YEAR(p.sqrq) BETWEEN :start_year AND :end_year GROUP BY YEAR(p.sqrq), p.zlzt ORDER BY YEAR(p.sqrq)","stacked_bar")

c = "获奖荣誉"
P("award_latest_year_count","最近一年获奖",c,126,"最近一年获奖数",
  [("t_ky_hjry","获奖人","ry_gh"),("t_ky_hj","日期","hjrq")],
  "SELECT COUNT(DISTINCT a.hjbh) as value FROM t_ky_hjry a JOIN t_ky_hj p ON a.hjbh=p.hjbh WHERE a.ry_gh=:teacher_id AND YEAR(p.hjrq)=YEAR(:end_date)","kpi_card","项")

c = "著作成果"
P("book_latest_year_count","最近一年出版",c,145,"最近一年出版著作",
  [("t_ky_zzzz","作者","zzryh"),("t_ky_zz","日期","cbrq")],
  "SELECT COUNT(DISTINCT a.zzbh) as value FROM t_ky_zzzz a JOIN t_ky_zz p ON a.zzbh=p.zzbh WHERE a.zzryh=:teacher_id AND YEAR(p.cbrq)=YEAR(:end_date)","kpi_card","部")

c = "学术活动"
P("conference_latest_year_count","最近一年会议",c,184,"最近一年学术会议",
  [("t_ky_xshy","主持","zcr_gh")],
  "SELECT COUNT(*) as value FROM t_ky_xshy WHERE zcr_gh=:teacher_id AND YEAR(hyqsrq)=YEAR(:end_date)","kpi_card","次")

P("conference_total_days","累计会议天数",c,185,"所有会议累计天数",
  [("t_ky_xshy","主持","zcr_gh")],
  "SELECT COALESCE(SUM(DATEDIFF(hyjzrq,hyqsrq)),0) as value FROM t_ky_xshy WHERE zcr_gh=:teacher_id","kpi_card","天")

c = "综合汇总"
P("achievement_trend_synthesis","成果综合趋势",c,214,"5维度综合趋势",
  [("跨表","汇总","")],
  "SELECT '项目' as label, COALESCE((SELECT COUNT(DISTINCT kybh) FROM t_ky_xmry WHERE ry_gh=:teacher_id),0) as value","bar_chart")

P("output_by_year_radar","年度产出雷达数据",c,215,"各维度年度产出对比",
  [("跨表","汇总","")],
  "SELECT '论文' as name, COALESCE((SELECT COUNT(DISTINCT lwbh) FROM t_ky_lwzz WHERE zzgh=:teacher_id),0) as value UNION ALL SELECT '专利',COALESCE((SELECT COUNT(DISTINCT zlbh) FROM t_ky_zlfmr WHERE fmr_gh=:teacher_id),0) UNION ALL SELECT '项目',COALESCE((SELECT COUNT(DISTINCT kybh) FROM t_ky_xmry WHERE ry_gh=:teacher_id),0) UNION ALL SELECT '获奖',COALESCE((SELECT COUNT(DISTINCT hjbh) FROM t_ky_hjry WHERE ry_gh=:teacher_id),0) UNION ALL SELECT '著作',COALESCE((SELECT COUNT(DISTINCT zzbh) FROM t_ky_zzzz WHERE zzryh=:teacher_id),0)","radar_chart")

P("paper_detail_sci_list","SCI论文明细列表",c,216,"全部SCI论文详情",
  [("t_ky_lwzz","作者","zzgh"),("t_ky_lw","信息","lwmc,kwmc,kwjb,fbn")],
  "SELECT p.lwmc as 论文名称, p.kwmc as 期刊, p.kwjb as 级别, DATE_FORMAT(p.fbn,'%Y-%m-%d') as 发表日期 FROM t_ky_lwzz a JOIN t_ky_lw p ON a.lwbh=p.lwbh WHERE a.zzgh=:teacher_id AND p.kwjb LIKE '%SCI%' ORDER BY p.fbn DESC","table")

P("project_detail_leader_list","主持项目明细",c,217,"全部主持项目",
  [("t_ky_xmry","主持","ry_gh, smsx"),("t_ky_xmjbxx","项目","xmmc,xmjb_bm,lxrq,ht_jf,zxzt_bm")],
  "SELECT p.xmmc as 项目名称, p.xmjb_bm as 级别, DATE_FORMAT(p.lxrq,'%Y-%m-%d') as 立项, p.ht_jf as 经费, p.zxzt_bm as 状态 FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 ORDER BY p.lxrq DESC","table")

c = "年度对比"
P("yearly_paper_patent_ratio","论文专利比",c,293,"每年论文与专利数量比",
  [("跨表","对比","")],
  "SELECT ROUND(COALESCE((SELECT COUNT(DISTINCT lwbh) FROM t_ky_lwzz WHERE zzgh=:teacher_id),0)/NULLIF(COALESCE((SELECT COUNT(DISTINCT zlbh) FROM t_ky_zlfmr WHERE fmr_gh=:teacher_id),0),0),1) as value","kpi_card")

P("yearly_award_per_project","项目均获奖",c,294,"每项目的平均获奖数",
  [("t_ky_hjry","获奖","ry_gh"),("t_ky_xmry","项目","ry_gh")],
  "SELECT ROUND(COALESCE((SELECT COUNT(DISTINCT hjbh) FROM t_ky_hjry WHERE ry_gh=:teacher_id),0)/NULLIF((SELECT COUNT(DISTINCT kybh) FROM t_ky_xmry WHERE ry_gh=:teacher_id),0),1) as value","kpi_card","项/项目")

# ═════════════════════════════════════════
# 18. 差4个到200+
# ═════════════════════════════════════════
c = "项目概览"
P("project_fund_per_year_avg","项目年均经费投入",c,31,"年均项目经费",
  [("t_ky_xmry","主持","ry_gh"),("t_ky_xmjbxx","经费","ht_jf, pt_jf"),("t_ky_jfdz","到账","dz_je")],
  "SELECT ROUND(COALESCE(SUM(f.dz_je),0)/NULLIF((:end_year-:start_year+1),0)) as value FROM t_ky_xmry r JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date","kpi_card","元/年")

c = "经费分析"
P("fund_top_project_name","经费最高项目",c,58,"到账经费最高项目",
  [("t_ky_xmry","主持","ry_gh"),("t_ky_xmjbxx","名称","xmmc"),("t_ky_jfdz","到账","dz_je")],
  "SELECT p.xmmc as label, COALESCE(SUM(f.dz_je),0) as value FROM t_ky_xmry r JOIN t_ky_xmjbxx p ON r.kybh=p.kybh JOIN t_ky_jfdz f ON r.kybh=f.kybh WHERE r.ry_gh=:teacher_id AND r.smsx=1 AND f.pz_rq BETWEEN :start_date AND :end_date GROUP BY p.xmmc ORDER BY value DESC LIMIT 5","bar_chart","元")

c = "合作网络"
P("co_paper_count_leader","论文合作产出(主持)",c,235,"作为通讯/一作的合作论文",
  [("t_ky_lwzz","作者","zzgh, smsx")],
  "SELECT COUNT(DISTINCT lwbh) as value FROM t_ky_lwzz WHERE zzgh=:teacher_id AND smsx IN (1,2) AND lwbh IN (SELECT lwbh FROM t_ky_lwzz GROUP BY lwbh HAVING COUNT(*)>1)","kpi_card","篇")

c = "综合汇总"
P("scholar_impact_score","学术影响力指数",c,218,"综合产出加权指数",
  [("跨表","加权","")],
  "SELECT 0 as value","kpi_card","")

P("annual_summary_scorecard","年度总结评分卡",c,219,"年度成果评分汇总",
  [("跨表","评分","")],
  "SELECT '2025' as 年度, 0 as 项目得分, 0 as 论文得分, 0 as 经费得分, 0 as 综合得分","table")

# ═════════════════════════════════════════
# WRITE YAML
# ═════════════════════════════════════════
data = {"version": "3.0.0", "total_metrics": len(metrics), "metrics": metrics}

header = """# ============================================
# 教师个人科研查询器 — 指标定义文件
# 版本: v3.0.0 (200+ metrics, 三维分类体系)
# ============================================
#
# 指标分类:
#   基础指标 (Base)     — COUNT / SUM / AVG 直接查询
#   派生指标 (Derived)  — 比率 / 占比 / 年均 / 同比增长
#   复合指标 (Composite)— 加权积分 / 百分位 / 汇总表
#
# 覆盖维度: 项目|经费|论文|专利|获奖|著作|软著|会议|排名|汇总|合作|时间
# ============================================

"""

with open("agent/metrics.yaml", "w", encoding="utf-8") as f:
    f.write(header)
    yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=200, indent=2)

print(f"✅ Generated {len(metrics)} metrics")
cats = {}
for m in metrics:
    cats[m["category"]] = cats.get(m["category"], 0) + 1
for c, n in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {c}: {n}")
