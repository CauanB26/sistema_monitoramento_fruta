import os
import json
import argparse
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.widgets import RangeSlider, Button, CheckButtons
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("THINGSPEAK_READ_API_KEY")
CHANNEL_ID = os.getenv("THINGSPEAK_CHANNEL_ID")
JSON_FALLBACK = "dados.json"

FIELDS = {
    "field1": ("Temperatura",   "°C",   "#FF6B6B"),
    "field2": ("Umidade",       "%",    "#4ECDC4"),
    "field3": ("Luminosidade",  "lux",  "#FFE66D"),
    "field4": ("Sinal MQ-3",    "ADC",  "#A8E6CF"),
    "field5": ("Sinal MQ-135",  "ADC",  "#C3A6FF"),
}


def parse_args():
    p = argparse.ArgumentParser(description="Plot amadurecimento de frutas")
    p.add_argument("--start",   help="Data inicial (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)")
    p.add_argument("--end",     help="Data final   (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)")
    p.add_argument("--days",    type=int, default=2,    help="Últimos N dias (padrão: 2)")
    p.add_argument("--results", type=int, default=8000, help="Máx. leituras por requisição")
    return p.parse_args()


def fetch_from_api(
    results: int = 8000,
    days: int = None,
    start: str = None,
    end: str = None,
) -> list[dict]:
    if not CHANNEL_ID:
        raise ValueError("THINGSPEAK_CHANNEL_ID não definido no .env")

    params = f"?api_key={API_KEY}&results={results}"

    # --start/--end têm prioridade sobre --days
    if start:
        params += f"&start={start.replace(' ', '%20')}"
    elif days:
        params += f"&days={days}"

    if end:
        params += f"&end={end.replace(' ', '%20')}"

    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json{params}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    feeds = resp.json()["feeds"]
    return feeds


def load_from_json(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("feeds", [])


def remove_outliers_iqr(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    for col in cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            # Distribuição degenerada (ex: maioria de zeros): IQR removeria
            # todos os valores fora da moda — pula esta coluna
            continue
        mask &= df[col].between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
    return df[mask]


def build_dataframe(feeds: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(feeds)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df["created_at"] = df["created_at"].dt.tz_convert("America/Sao_Paulo")

    numeric_cols = list(FIELDS.keys())
    for col in numeric_cols:
        df[col] = pd.to_numeric(df.get(col), errors="coerce")

    df = df[df["field4"].notna() & (df["field4"] != 0)]
    df = df[df["field5"].notna() & (df["field5"] != 0)]
    df = df.dropna(subset=numeric_cols)
    df = remove_outliers_iqr(df, numeric_cols)
    df = df.sort_values("created_at").reset_index(drop=True)
    return df


def apply_date_filter(df: pd.DataFrame, start: str = None, end: str = None) -> pd.DataFrame:
    tz = df["created_at"].dt.tz
    if start:
        ts = pd.Timestamp(start).tz_localize(tz) if pd.Timestamp(start).tzinfo is None else pd.Timestamp(start).tz_convert(tz)
        df = df[df["created_at"] >= ts]
    if end:
        ts = pd.Timestamp(end).tz_localize(tz) if pd.Timestamp(end).tzinfo is None else pd.Timestamp(end).tz_convert(tz)
        df = df[df["created_at"] <= ts]
    return df


def moving_average(series: pd.Series, window: int = 5) -> pd.Series:
    return series.rolling(window=window, center=True, min_periods=1).mean()


def plot(df: pd.DataFrame) -> None:
    plt.style.use("dark_background")

    fig = plt.figure(figsize=(16, 22))
    fig.patch.set_facecolor("#0e0e0e")

    # Subplots à esquerda; lado direito reservado para checkboxes
    gs = fig.add_gridspec(5, 1, left=0.05, right=0.76, top=0.965, bottom=0.14, hspace=0.35)
    axes = [fig.add_subplot(gs[i]) for i in range(5)]

    tz = df["created_at"].dt.tz
    x_full = df["created_at"]
    t_num = mdates.date2num(x_full.dt.to_pydatetime())
    t_min, t_max = t_num.min(), t_num.max()
    date_fmt = mdates.DateFormatter("%d/%m %H:%M", tz=tz)

    field_keys   = list(FIELDS.keys())
    field_titles = [v[0] for v in FIELDS.values()]
    field_colors = [v[2] for v in FIELDS.values()]

    lines_raw, lines_smooth = [], []
    for ax, (field, (title, unit, color)) in zip(axes, FIELDS.items()):
        raw = df[field]
        smooth = moving_average(raw)
        (lr,) = ax.plot(x_full, raw,    color=color, alpha=0.22, linewidth=0.8)
        (ls,) = ax.plot(x_full, smooth, color=color, linewidth=2)
        lines_raw.append(lr)
        lines_smooth.append(ls)

        ax.set_title(title, fontsize=10, color=color, pad=3)
        ax.set_ylabel(unit, fontsize=9, color="white")
        ax.grid(True, linestyle="--", alpha=0.25)
        ax.tick_params(colors="white", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333333")
        ax.xaxis.set_major_formatter(date_fmt)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())

    def _sync_xticklabels():
        """Mostra rótulos de data apenas no último eixo visível."""
        visible = [ax for ax in axes if ax.get_visible()]
        for ax in axes:
            is_bottom = ax.get_visible() and bool(visible) and ax is visible[-1]
            ax.tick_params(axis="x", labelbottom=is_bottom)
            if is_bottom:
                for lbl in ax.get_xticklabels():
                    lbl.set_rotation(30)
                    lbl.set_ha("right")

    _sync_xticklabels()

    # ── CheckButtons — filtro de sensor ──────────────────────────────────────
    ax_check = fig.add_axes([0.79, 0.22, 0.185, 0.72], facecolor="#111111")
    ax_check.set_title("Sensores", color="#aaaaaa", fontsize=9, pad=8)
    for spine in ax_check.spines.values():
        spine.set_edgecolor("#333333")

    check = CheckButtons(ax_check, field_titles, [True] * 5)

    # Estiliza labels (funciona em todas as versões do matplotlib)
    for i, lbl in enumerate(check.labels):
        lbl.set_color(field_colors[i])
        lbl.set_fontsize(9)

    # Estiliza caixas de seleção — API mudou no matplotlib 3.7+
    try:
        for i, rect in enumerate(check.rectangles):
            rect.set_edgecolor(field_colors[i])
            rect.set_facecolor(field_colors[i])
            rect.set_alpha(0.55)
    except AttributeError:
        pass

    try:
        for pair in check.lines:
            for ln in pair:
                ln.set_color("white")
                ln.set_linewidth(1.8)
    except (AttributeError, TypeError):
        pass

    def toggle(label):
        idx = field_titles.index(label)
        axes[idx].set_visible(not axes[idx].get_visible())
        _sync_xticklabels()
        fig.canvas.draw_idle()

    check.on_clicked(toggle)

    # ── Slider de intervalo de data ──────────────────────────────────────────
    ax_slider = fig.add_axes([0.05, 0.075, 0.68, 0.022], facecolor="#1a1a1a")
    slider = RangeSlider(
        ax_slider, "", t_min, t_max,
        valinit=(t_min, t_max),
        color="#4ECDC4",
    )
    slider.label.set_visible(False)
    slider.valtext.set_visible(False)

    label_text = fig.text(
        0.38, 0.055,
        _fmt_range(t_min, t_max, tz=tz),
        ha="center", va="center",
        fontsize=9, color="#cccccc",
    )

    # ── Botão Exportar PNG ────────────────────────────────────────────────────
    ax_btn = fig.add_axes([0.79, 0.065, 0.11, 0.032])
    btn = Button(ax_btn, "Exportar PNG", color="#1e3a3a", hovercolor="#2e5a5a")
    btn.label.set_color("#4ECDC4")
    btn.label.set_fontsize(8)

    # ── Callbacks ────────────────────────────────────────────────────────────
    def update(val):
        lo, hi = slider.val
        dt_lo = pd.Timestamp(mdates.num2date(lo)).tz_convert(tz)
        dt_hi = pd.Timestamp(mdates.num2date(hi)).tz_convert(tz)

        mask = (df["created_at"] >= dt_lo) & (df["created_at"] <= dt_hi)
        df_f = df[mask]
        x_f = df_f["created_at"]

        for i, field in enumerate(field_keys):
            lines_raw[i].set_data(x_f, df_f[field])
            lines_smooth[i].set_data(x_f, moving_average(df_f[field]))

        for ax in axes:
            ax.relim()
            ax.autoscale_view()

        label_text.set_text(_fmt_range(lo, hi, tz=tz))
        fig.canvas.draw_idle()

    def export(_event):
        lo, hi = slider.val
        dt_lo = pd.Timestamp(mdates.num2date(lo, tz=tz))
        dt_hi = pd.Timestamp(mdates.num2date(hi, tz=tz))
        active = [field_titles[i] for i, ax in enumerate(axes) if ax.get_visible()]
        sensors = "_".join(t[:4] for t in active) or "none"
        fname = (
            f"monitoramento_{sensors}_"
            f"{dt_lo.strftime('%Y%m%d_%H%M')}_"
            f"{dt_hi.strftime('%Y%m%d_%H%M')}.png"
        )
        fig.savefig(fname, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
        print(f"Exportado: {fname}")

    slider.on_changed(update)
    btn.on_clicked(export)

    plt.show()


def _fmt_range(lo: float, hi: float, tz=None) -> str:
    fmt = "%d/%m/%Y %H:%M"
    return (
        f"{mdates.num2date(lo, tz=tz).strftime(fmt)}  →  "
        f"{mdates.num2date(hi, tz=tz).strftime(fmt)}"
    )


def main() -> None:
    args = parse_args()
    feeds = None

    if CHANNEL_ID:
        try:
            modo = f"--start {args.start}" if args.start else f"--days {args.days}"
            print(f"Buscando dados da API ThingSpeak ({modo})...")
            feeds = fetch_from_api(
                results=args.results,
                days=args.days,
                start=args.start,
                end=args.end,
            )
            print(f"{len(feeds)} leituras obtidas.")
        except Exception as exc:
            print(f"Erro na API: {exc}. Tentando arquivo local...")

    if feeds is None:
        print(f"Lendo arquivo local: {JSON_FALLBACK}")
        feeds = load_from_json(JSON_FALLBACK)

    df = build_dataframe(feeds)

    if args.start or args.end:
        df = apply_date_filter(df, args.start, args.end)

    print(f"Leituras após limpeza: {len(df)}")
    if not df.empty:
        print(f"Intervalo: {df['created_at'].min()}  →  {df['created_at'].max()}")
    print(df[["created_at"] + list(FIELDS.keys())].tail())

    plot(df)


if __name__ == "__main__":
    main()
