from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "woodlogistics.db"

app = Flask(__name__)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                wood_type TEXT NOT NULL,
                quality_grade TEXT NOT NULL,
                volume_m3 REAL NOT NULL,
                estimated_value REAL NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'in_stock',
                shipment_id INTEGER,
                FOREIGN KEY (shipment_id) REFERENCES shipments(id)
            );

            CREATE TABLE IF NOT EXISTS shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                truck_number TEXT UNIQUE NOT NULL,
                driver_name TEXT NOT NULL,
                destination TEXT NOT NULL,
                shipping_cost REAL NOT NULL,
                sale_value REAL NOT NULL,
                created_at TEXT NOT NULL,
                total_volume REAL NOT NULL,
                profit REAL NOT NULL
            );
            """
        )


def query_one(query: str, params: tuple[Any, ...] = ()) -> Any:
    with get_db() as conn:
        return conn.execute(query, params).fetchone()


def query_all(query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(query, params).fetchall()


@app.route("/")
def dashboard() -> str:
    overview = query_one(
        """
        SELECT
            COUNT(*) AS total_batches,
            SUM(CASE WHEN status = 'in_stock' THEN 1 ELSE 0 END) AS in_stock_batches,
            COALESCE(SUM(CASE WHEN status = 'in_stock' THEN volume_m3 ELSE 0 END), 0) AS in_stock_volume,
            COALESCE(SUM(CASE WHEN status = 'shipped' THEN estimated_value ELSE 0 END), 0) AS shipped_value
        FROM batches
        """
    )

    shipment_stats = query_one(
        """
        SELECT
            COUNT(*) AS total_shipments,
            COALESCE(SUM(sale_value), 0) AS revenue,
            COALESCE(SUM(shipping_cost), 0) AS costs,
            COALESCE(SUM(profit), 0) AS profit
        FROM shipments
        """
    )

    wood_breakdown = query_all(
        """
        SELECT wood_type, COUNT(*) AS amount
        FROM batches
        WHERE status = 'in_stock'
        GROUP BY wood_type
        ORDER BY amount DESC
        """
    )

    monthly_profit = query_all(
        """
        SELECT substr(created_at, 1, 7) AS month, SUM(profit) AS total_profit
        FROM shipments
        GROUP BY month
        ORDER BY month
        """
    )

    recent_shipments = query_all(
        """
        SELECT truck_number, destination, total_volume, profit, created_at
        FROM shipments
        ORDER BY id DESC
        LIMIT 5
        """
    )

    return render_template(
        "dashboard.html",
        overview=overview,
        shipment_stats=shipment_stats,
        wood_breakdown=wood_breakdown,
        monthly_profit=monthly_profit,
        recent_shipments=recent_shipments,
    )


@app.route("/warehouse", methods=["GET", "POST"])
def warehouse() -> str:
    if request.method == "POST":
        code = request.form["code"].strip()
        wood_type = request.form["wood_type"].strip()
        quality_grade = request.form["quality_grade"].strip()
        volume_m3 = float(request.form["volume_m3"])
        estimated_value = float(request.form["estimated_value"])

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO batches (code, wood_type, quality_grade, volume_m3, estimated_value, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (code, wood_type, quality_grade, volume_m3, estimated_value, datetime.now().isoformat()),
            )

        return redirect(url_for("warehouse"))

    batches = query_all(
        """
        SELECT id, code, wood_type, quality_grade, volume_m3, estimated_value, created_at, status
        FROM batches
        ORDER BY id DESC
        """
    )
    return render_template("warehouse.html", batches=batches)


@app.route("/shipments", methods=["GET", "POST"])
def shipments() -> str:
    if request.method == "POST":
        selected_ids = [int(batch_id) for batch_id in request.form.getlist("batch_ids")]
        if selected_ids:
            truck_number = request.form["truck_number"].strip()
            driver_name = request.form["driver_name"].strip()
            destination = request.form["destination"].strip()
            shipping_cost = float(request.form["shipping_cost"])
            sale_value = float(request.form["sale_value"])

            placeholders = ",".join(["?"] * len(selected_ids))
            selected_batches = query_all(
                f"SELECT id, volume_m3 FROM batches WHERE id IN ({placeholders}) AND status = 'in_stock'",
                tuple(selected_ids),
            )

            total_volume = sum(batch["volume_m3"] for batch in selected_batches)
            profit = sale_value - shipping_cost

            with get_db() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO shipments (
                        truck_number, driver_name, destination,
                        shipping_cost, sale_value, created_at, total_volume, profit
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        truck_number,
                        driver_name,
                        destination,
                        shipping_cost,
                        sale_value,
                        datetime.now().isoformat(),
                        total_volume,
                        profit,
                    ),
                )
                shipment_id = cursor.lastrowid

                conn.execute(
                    f"UPDATE batches SET status = 'shipped', shipment_id = ? WHERE id IN ({placeholders})",
                    (shipment_id, *selected_ids),
                )

        return redirect(url_for("shipments"))

    available_batches = query_all(
        """
        SELECT id, code, wood_type, quality_grade, volume_m3, estimated_value
        FROM batches
        WHERE status = 'in_stock'
        ORDER BY created_at ASC
        """
    )

    shipment_history = query_all(
        """
        SELECT id, truck_number, driver_name, destination, total_volume, sale_value, shipping_cost, profit, created_at
        FROM shipments
        ORDER BY id DESC
        LIMIT 8
        """
    )

    return render_template(
        "shipments.html",
        available_batches=available_batches,
        shipment_history=shipment_history,
    )


@app.route("/archive")
def archive() -> str:
    archived = query_all(
        """
        SELECT
            s.truck_number,
            s.driver_name,
            s.destination,
            s.total_volume,
            s.profit,
            s.created_at,
            GROUP_CONCAT(b.code, ', ') AS batch_codes
        FROM shipments s
        LEFT JOIN batches b ON b.shipment_id = s.id
        GROUP BY s.id
        ORDER BY s.id DESC
        """
    )
    return render_template("archive.html", archived=archived)


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
