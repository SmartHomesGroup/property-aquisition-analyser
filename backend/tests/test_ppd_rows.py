from pathlib import Path

from paa.etl.ppd import _rows

ROW_15 = '"{A}","250000","2024-03-01 00:00","N11 2AB","T","N","F","12","","EXAMPLE ROAD","","LONDON","BARNET","GREATER LONDON","A"'
ROW_16 = '"{B}","300000","2024-04-01 00:00","EN1 1AA","S","N","F","3","","OTHER ROAD","","ENFIELD","ENFIELD","GREATER LONDON","A","A"'
ROW_NW = '"{C}","300000","2024-04-01 00:00","NW1 1AA","F","N","L","FLAT 1","9","HIGH ST","","LONDON","CAMDEN","GREATER LONDON","A","A"'


def test_rows_pad_and_filter(tmp_path: Path) -> None:
    f = tmp_path / "pp.csv"
    f.write_text("\n".join([ROW_15, ROW_16, ROW_NW]) + "\n")

    rows = list(_rows(f, []))
    assert [len(r) for r in rows] == [16, 16, 16]
    assert rows[0][15] == "A"

    # "N" must match N11 but not NW1; "EN" matches EN1.
    rows = list(_rows(f, ["N", "EN"]))
    assert [r[3] for r in rows] == ["N11 2AB", "EN1 1AA"]
