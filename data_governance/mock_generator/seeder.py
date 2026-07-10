"""
Mock 数据灌入脚本 — 连接 MySQL，清空旧数据，批量插入 Mock 数据
"""
import sys
sys.path.insert(0, '..')

import pymysql
from generator import generate_all, MockData

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "tr_user",
    "password": "tr_pass_2025",
    "database": "teacher_research",
    "charset": "utf8mb4",
}


def get_conn():
    return pymysql.connect(**DB_CONFIG)


def clear_all(cursor):
    """清空所有表（按外键依赖倒序）"""
    tables = [
        "t_ky_hjry","t_ky_hj",
        "t_ky_lwzz","t_ky_lw",
        "t_ky_zlfmr","t_ky_zl",
        "t_ky_zzzz","t_ky_zz",
        "t_ky_rjzzcy","t_ky_rjzz",
        "t_ky_jfwb","t_ky_jfzc","t_ky_jfdz",
        "t_ky_xmry","t_ky_xmjbxx",
        "t_ky_xshy",
        "t_ky_kyjgry","t_ky_kyjg",
        "t_jzg_jbxx",
    ]
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    for table in tables:
        cursor.execute(f"TRUNCATE TABLE {table}")
    cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    print(f"  清空 {len(tables)} 张表 — 完成")


def insert_teachers(conn, cursor, data: MockData):
    """插入教师"""
    sql = """INSERT INTO t_jzg_jbxx (id, gh, xm, xb, dw_bm, dw_mc, zc, xkml_bm, ryrq)
             VALUES (%(id)s, %(gh)s, %(xm)s, %(xb)s, %(dw_bm)s, %(dw_mc)s, %(zc)s, %(xkml_bm)s, %(ryrq)s)"""
    cursor.executemany(sql, data.teachers)
    conn.commit()
    print(f"  教师: {len(data.teachers)} 人")


def insert_projects(conn, cursor, data: MockData):
    """插入项目 + 人员关系"""
    sql1 = """INSERT INTO t_ky_xmjbxx (id, kybh, xmmc, xmbh_xn, ssdw_bm, xmlx_bm, xmxz_bm,
               xmjb_bm, xkml_bm, lxrq, ksrq, jxrq, jhwcrq, fzr_gh, ht_jf, pt_jf, zxzt_bm, htbh, jfkh)
              VALUES (%(id)s, %(kybh)s, %(xmmc)s, %(xmbh_xn)s, %(ssdw_bm)s, %(xmlx_bm)s, %(xmxz_bm)s,
                %(xmjb_bm)s, %(xkml_bm)s, %(lxrq)s, %(ksrq)s, %(jxrq)s, %(jhwcrq)s,
                %(fzr_gh)s, %(ht_jf)s, %(pt_jf)s, %(zxzt_bm)s, %(htbh)s, %(jfkh)s)"""
    sql2 = """INSERT INTO t_ky_xmry (kybh, ry_gh, ry_xm, dw_bm, rylx_bm, ryjs_bm, smsx, gxl)
              VALUES (%(kybh)s, %(ry_gh)s, %(ry_xm)s, %(dw_bm)s, %(rylx_bm)s, %(ryjs_bm)s, %(smsx)s, %(gxl)s)"""
    cursor.executemany(sql1, data.projects)
    cursor.executemany(sql2, data.project_members)
    conn.commit()
    print(f"  项目: {len(data.projects)} 个, 人员关系: {len(data.project_members)} 条")


def insert_funding(conn, cursor, data: MockData):
    """插入经费数据"""
    sql1 = """INSERT INTO t_ky_jfdz (cw_xmbh, kybh, km_bh, km_mc, kj_nd, pz_rq, dz_je)
              VALUES (%(cw_xmbh)s, %(kybh)s, %(km_bh)s, %(km_mc)s, %(kj_nd)s, %(pz_rq)s, %(dz_je)s)"""
    sql2 = """INSERT INTO t_ky_jfzc (cw_xmbh, kybh, km_bh, km_mc, kj_nd, pz_rq, zc_je)
              VALUES (%(cw_xmbh)s, %(kybh)s, %(km_bh)s, %(km_mc)s, %(kj_nd)s, %(pz_rq)s, %(zc_je)s)"""
    sql3 = """INSERT INTO t_ky_jfwb (cw_xmbh, kybh, km_bh, km_mc, kj_nd, pz_rq, wb_je)
              VALUES (%(cw_xmbh)s, %(kybh)s, %(km_bh)s, %(km_mc)s, %(kj_nd)s, %(pz_rq)s, %(wb_je)s)"""
    cursor.executemany(sql1, data.fund_arrivals)
    cursor.executemany(sql2, data.fund_expenses)
    cursor.executemany(sql3, data.fund_transfers)
    conn.commit()
    print(f"  到账: {len(data.fund_arrivals)} 条, 支出: {len(data.fund_expenses)} 条, 外拨: {len(data.fund_transfers)} 条")


def insert_papers(conn, cursor, data: MockData):
    """插入论文"""
    sql1 = """INSERT INTO t_ky_lw (id, lwbh, lwmc, lwywmc, kwmc, kwjb, slqk, fbn, fbq, xkml_bm, kybh)
              VALUES (%(id)s, %(lwbh)s, %(lwmc)s, %(lwywmc)s, %(kwmc)s, %(kwjb)s, %(slqk)s, %(fbn)s, %(fbq)s, %(xkml_bm)s, %(kybh)s)"""
    sql2 = """INSERT INTO t_ky_lwzz (lwbh, zzgh, zzxm, dwbm, smsx, gxl)
              VALUES (%(lwbh)s, %(zzgh)s, %(zzxm)s, %(dwbm)s, %(smsx)s, %(gxl)s)"""
    cursor.executemany(sql1, data.papers)
    cursor.executemany(sql2, data.paper_authors)
    conn.commit()
    print(f"  论文: {len(data.papers)} 篇, 作者: {len(data.paper_authors)} 人次")


def insert_patents(conn, cursor, data: MockData):
    sql1 = """INSERT INTO t_ky_zl (id, zlbh, zlmc, zllx, zlzt, sqrq, sqrq2, kybh)
              VALUES (%(id)s, %(zlbh)s, %(zlmc)s, %(zllx)s, %(zlzt)s, %(sqrq)s, %(sqrq2)s, %(kybh)s)"""
    sql2 = """INSERT INTO t_ky_zlfmr (zlbh, fmr_gh, fmr_xm, smsx)
              VALUES (%(zlbh)s, %(fmr_gh)s, %(fmr_xm)s, %(smsx)s)"""
    cursor.executemany(sql1, data.patents)
    cursor.executemany(sql2, data.patent_inventors)
    conn.commit()
    print(f"  专利: {len(data.patents)} 项, 发明人: {len(data.patent_inventors)} 人次")


def insert_books(conn, cursor, data: MockData):
    sql1 = """INSERT INTO t_ky_zz (id, zzbh, zzmc, cbs, cbrq, isbn, lzlbm, yzm, sfsmbx, zzzs, kybh)
              VALUES (%(id)s, %(zzbh)s, %(zzmc)s, %(cbs)s, %(cbrq)s, %(isbn)s, %(lzlbm)s, %(yzm)s, %(sfsmbx)s, %(zzzs)s, %(kybh)s)"""
    sql2 = """INSERT INTO t_ky_zzzz (zzbh, zzryh, zzxm, cdjs, smsx, gxl)
              VALUES (%(zzbh)s, %(zzryh)s, %(zzxm)s, %(cdjs)s, %(smsx)s, %(gxl)s)"""
    cursor.executemany(sql1, data.books)
    cursor.executemany(sql2, data.book_authors)
    conn.commit()
    print(f"  著作: {len(data.books)} 本, 作者: {len(data.book_authors)} 人次")


def insert_software(conn, cursor, data: MockData):
    sql1 = """INSERT INTO t_ky_rjzz (id, rjzzbh, rjzzmc, rjzzdjh, djrq, kybh)
              VALUES (%(id)s, %(rjzzbh)s, %(rjzzmc)s, %(rjzzdjh)s, %(djrq)s, %(kybh)s)"""
    sql2 = """INSERT INTO t_ky_rjzzcy (rjzzbh, zzryh, zzxm, smsx)
              VALUES (%(rjzzbh)s, %(zzryh)s, %(zzxm)s, %(smsx)s)"""
    cursor.executemany(sql1, data.software)
    cursor.executemany(sql2, data.software_members)
    conn.commit()
    print(f"  软著: {len(data.software)} 项, 成员: {len(data.software_members)} 人次")


def insert_awards(conn, cursor, data: MockData):
    sql1 = """INSERT INTO t_ky_hj (id, hjbh, hjmc, hjjb, hjrq, bjdw, kybh)
              VALUES (%(id)s, %(hjbh)s, %(hjmc)s, %(hjjb)s, %(bjrq)s, %(bjdw)s, %(kybh)s)"""
    sql2 = """INSERT INTO t_ky_hjry (hjbh, ry_gh, ry_xm, smsx)
              VALUES (%(hjbh)s, %(ry_gh)s, %(ry_xm)s, %(smsx)s)"""
    cursor.executemany(sql1, data.awards)
    cursor.executemany(sql2, data.award_members)
    conn.commit()
    print(f"  获奖: {len(data.awards)} 项, 人员: {len(data.award_members)} 人次")


def insert_conferences(conn, cursor, data: MockData):
    sql = """INSERT INTO t_ky_xshy (id, hybh, hymc, hydd, hyqsrq, hyjzrq, hydj, hyrs, trjf, zcr_gh, lwps, tybgps)
             VALUES (%(id)s, %(hybh)s, %(hymc)s, %(hydd)s, %(hyqsrq)s, %(hyjzrq)s, %(hydj)s, %(hyrs)s, %(trjf)s, %(zcr_gh)s, %(lwps)s, %(tybgps)s)"""
    cursor.executemany(sql, data.conferences)
    conn.commit()
    print(f"  会议: {len(data.conferences)} 个")


def insert_institutions(conn, cursor, data: MockData):
    sql1 = """INSERT INTO t_ky_kyjg (id, jgbh, jgmc, gkdwbm, fzr_gh, xkmlm, jglbm, jgjbm, sfstjg)
              VALUES (%(id)s, %(jgbh)s, %(jgmc)s, %(gkdwbm)s, %(fzr_gh)s, %(xkmlm)s, %(jglbm)s, %(jgjbm)s, %(sfstjg)s)"""
    sql2 = """INSERT INTO t_ky_kyjgry (jgbh, ry_gh, ry_xm, xkmlm, yjfx)
              VALUES (%(jgbh)s, %(ry_gh)s, %(ry_xm)s, %(xkmlm)s, %(yjfx)s)"""
    cursor.executemany(sql1, data.institutions)
    cursor.executemany(sql2, data.institution_members)
    conn.commit()
    print(f"  科研机构: {len(data.institutions)} 个, 成员: {len(data.institution_members)} 人次")


if __name__ == "__main__":
    print("=" * 60)
    print("Mock 数据灌入开始")
    print("=" * 60)
    
    # 生成数据
    data = generate_all()
    
    # 连接 MySQL
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 清空旧数据
        print("\n清空旧数据...")
        clear_all(cursor)
        conn.commit()
        
        # 按依赖顺序插入
        print("\n插入数据...")
        insert_teachers(conn, cursor, data)
        insert_projects(conn, cursor, data)
        insert_funding(conn, cursor, data)
        insert_papers(conn, cursor, data)
        insert_patents(conn, cursor, data)
        insert_books(conn, cursor, data)
        insert_software(conn, cursor, data)
        insert_awards(conn, cursor, data)
        insert_conferences(conn, cursor, data)
        insert_institutions(conn, cursor, data)
        
        print("\n" + "=" * 60)
        print("✅ 全部数据灌入完成！")
        print("=" * 60)
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 错误: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
