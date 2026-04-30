import time
import statistics
import smtplib
import os
import logging
from email.mime.text import MIMEText
import speedtest
from dotenv import load_dotenv
load_dotenv()


# ================= CONFIG =================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

REFERENCE_SPEED = float(os.getenv("REFERENCE_SPEED", 600))

# Thresholds
THRESHOLD_OK = 0.7
THRESHOLD_CRITICAL = 0.5

# ================= LOG =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("monitor.log"),
        logging.StreamHandler()
    ]
)

# ================= EMAIL =================
def send_email(subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())

        logging.info("Email enviado com sucesso")

    except Exception as e:
        logging.error(f"Erro ao enviar email: {e}")

# ================= SPEED =================
def check_speed():
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        return st.download() / 1_000_000
    except Exception as e:
        logging.error(f"Erro no speedtest: {e}")
        return 0

# ================= STATUS =================
def get_status(avg_speed):
    if avg_speed < THRESHOLD_CRITICAL * REFERENCE_SPEED:
        return "CRITICO"
    elif avg_speed < THRESHOLD_OK * REFERENCE_SPEED:
        return "RUIM"
    else:
        return "OK"

# ================= MAIN =================
def main():
    results = []
    last_status = None

    logging.info("Monitoramento iniciado...")

    while True:
        try:
            speed = check_speed()
            results.append(speed)

            logging.info(f"Velocidade atual: {speed:.2f} Mbps")

            if len(results) == 3:  # reduzido para teste rápido
                avg_speed = statistics.mean(results)
                status = get_status(avg_speed)

                logging.info(f"Média dos últimos testes: {avg_speed:.2f} Mbps | Status: {status}")

                # Envia email só se mudar status
                if status != last_status:
                    subject = f"Alerta Internet: {status}"
                    body = (
                        f"Status: {status}\n"
                        f"Velocidade média: {avg_speed:.2f} Mbps\n"
                        f"Plano: {REFERENCE_SPEED} Mbps\n"
                    )
                    send_email(subject, body)
                    last_status = status

                results.clear()

        except Exception as e:
            logging.error(f"Erro no loop principal: {e}")

        time.sleep(600)  # reduzido para teste rápido

# ================= START =================
if __name__ == "__main__":
    main()
