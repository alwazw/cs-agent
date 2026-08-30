# Autonomous Customer Communication Engine: Client User Manual & Operations Guide

Welcome to your Autonomous Chatbot Command Center! This document details how your team operates the AI assistant, handles live customer text interactions, manages calendar appointments, and monitors system alerts.

---

## 1. How the System Works for Your Business

Your AI Chatbot acts as an instant 24/7 front desk that responds to incoming customer SMS messages in under 3 seconds.

* **No Customer App Required:** Clients simply text your dedicated business phone number.
* **Smart Documentation Lookup:** The AI reads your company FAQs and services stored securely on private local hardware.
* **Dynamic Personas:** Route different phone numbers to specific tones (e.g., Support vs. VIP Concierge).

---

## 2. Default Port Mapping & Web Interfaces

To avoid port collisions on existing infrastructure, the service defaults to non-conflicting port ranges:

* **C2 Backend & API Docs:** `http://localhost:9876/docs` (configurable via `C2_PORT`)
* **Open WebUI Interface:** `http://localhost:9875` (configurable via `WEBUI_PORT`)
* **Redis Session Store:** `localhost:9874` (configurable via `REDIS_HOST_PORT`)

---

## 3. Customer Interaction & Conversation Flow

Below is the standard workflow from incoming text to resolution or live-agent handoff:

1. **Step 1: Inbound Text Request**
   Customer texts your dedicated business line asking about services, pricing, or appointment availability.
2. **Step 2: AI Knowledge Synthesis**
   The system scans your `/docs` folder for exact policy or service details and generates an accurate, tailored SMS reply.
3. **Step 3: Human-in-the-Loop (HITL) Handoff**
   If a customer asks for a human or types terms like `agent`, `human`, or `operator`, the system shifts the session state to `HUMAN_REQUESTED` and alerts your live dashboard queue.
4. **Step 4: Live Agent Intervention**
   Your team can claim the conversation in Open WebUI / C2 Dashboard, text back directly, or trigger a manual calendar booking.

---

## 4. Step-by-Step Guide: Booking Appointments & Override Feature

Standard bookings can trigger payment links. When you need to book an appointment directly (VIP client, internal bypass, or offline payment):

* **Step 1:** Open the **C2 Control Dashboard** and navigate to the **Live Conversations** tab.
* **Step 2:** Select the customer session requiring a manual schedule.
* **Step 3:** Click **"Bypass Payment & Book"**.
* **Step 4:** Select the date, time, and service requested.
* **Step 5:** Submit the request. The backend immediately creates the calendar event, updates the database state to `BOOKED_UNPAID_OVERRIDE`, and fires an automated SMS to the customer containing their Google Meet / Calendar confirmation link.

---

## 5. Notification Center & System Monitoring

The Notification Center tracks stack health and unexpected usage surges:

* **Token Consumption Alerts:** Triggers a `WARNING` or `CRITICAL` alert if token generation rapidly spikes (indicating runaway loops or scrapers).
* **Stack Health Status:** Monitors model engine latency and database connection integrity.
* **Simulated Demo Environment:** Click **"Run Simulation Test"** under Dashboard Settings or POST to `/api/c2/demo/simulate` to test system alert triggers without impacting production channels.

---

## 6. Editing Company Knowledge Base & FAQs Live

You do not need developers to change your bot's answers or business details:

1. Navigate to the **Knowledge Base** tab in the C2 Dashboard.
2. Select any `.md` file (e.g., `company_info.md`, `faq.md`, or `sales/pricing.md`).
3. Make your edits directly in the web markdown editor.
4. Click **Save File**. Changes take effect instantly across all incoming SMS chats—no server restarts needed.

---

## 7. Compliance & Carrier Opt-Out Keywords

The system automatically manages carrier compliance requirements:
* If a client texts `STOP` or `UNSUBSCRIBE`, the bot immediately pauses responses and marks the number as opted out.
* To resume automated responses, the client must text `START` or `SUBSCRIBE`.
