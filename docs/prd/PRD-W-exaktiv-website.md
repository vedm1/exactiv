# PRD-W — Exaktiv capability website

Version 1.0 · 18 November 2026 · Status: draft for design · Written in ASD-STE100
Live doc: https://claude.ai/artifact/29udQNzXYCk2mE2QbYPZ16 (the live doc is the master copy; re-export after edits)

## 1. Summary and goals

Exaktiv launches a global, English, capability-only website. It tells buyers what we do, how we protect their code and data, and how to contact us. The first user is a European software vendor that asked for a legacy modernisation proposal. Every later sales conversation uses the same site.

**Background.** Exaktiv is an AI venture. Its core idea is "no value without a source": every AI output links to the place it came from. The product engine is in build. Services start now.

**Promise of the site:** AI you can audit, with EU-level security and AI processing that stays in the client's region.

| Goal | Measure | Target |
| --- | --- | --- |
| A buyer understands what we do | Time to understand the offer on the home page | 10 seconds or less |
| A buyer can contact us | Clicks from any page to the contact route | 2 or fewer |
| A security reviewer trusts our data handling | Security page answers the standard questions (where, who, how long, which models) | All answered on one page |
| We reply fast | Time from form submission to first human reply | 1 business day or less |
| No exposure of individuals | Personal names, employer names or client names on the site | Zero |

At launch there is no analytics tool. We measure through the form and the inbox.

## 2. Non-goals and hard constraints

These rules are not open for design choice. A page that breaks one does not go live.

1. **No personal names.** No founder or team names, photos, LinkedIn links or personal email addresses. The site shows combined team experience only. The company name, Valyrian Tech Pvt Ltd, stands on one line of the privacy notice (the controller) and nowhere else on the site. No person is named. (Decision of 19 Nov 2026, EXW3.)
2. **No employer names.** Do not name any current or past employer of the team.
3. **No client names or logos.** No case study that can identify a client. Describe past work by sector and size only.
4. **No pricing.** Prices go in proposals.
5. **Global, not country-targeted.** English only (en-GB spelling). No German-language pages, no country domain such as .de, no single-country currency, no offers addressed to one country.
6. **No blog or news at launch.**
7. **No self-serve product.** Product pages say "early access". No sign-up or login.
8. **No cookies and no third-party trackers at launch.** So the site needs no cookie banner.
9. **No certification claims we do not hold** (for example ISO 27001 or SOC 2).
10. **Legal notice (Impressum) is phase 2.** It goes live when the first client contract is close. Section 11 lists the risk of this choice.

## 3. Audience and personas

The main reader is an engineering leader at a software vendor who got our link in an email. Most visitors arrive from a link we sent, not from search.

| Persona | What they need to know | What convinces them | Page they go to |
| --- | --- | --- | --- |
| Engineering leader (CTO, VP Engineering) at a software vendor | Can we modernise legacy code without stopping the roadmap? | A traceable method, a staged offer, low risk | Legacy Modernisation |
| Head of Product | Can we help ship AI features that customers use? | Delivery experience, AI skills, a clear way to start | AI Product Delivery |
| Security or compliance reviewer | Where does our code and data go, who sees it, which AI models touch it? | Specific answers: regions, retention, no training, human approval | Security and data handling |
| Procurement | Who are they, and how do we contract? | A clear contact route. The controller is named in the privacy notice (the legal notice in phase 2 names the contracting entity) | Contact, privacy notice |
| Partner agency | Can they add AI product or modernisation capacity to our projects? | Capability list, fast reply | Contact |

## 4. Positioning, messaging and voice

**Core claim:** "AI you can audit. Every finding traced to its source."

Every page supports one or more of the four proof pillars below. These pillars also exist as guardrails in the Exaktiv engine, so the site promises only what the engine enforces.

| Pillar | What it means for the client | Engine guardrail |
| --- | --- | --- |
| Traceable | Every finding links to its source: a file and a line in code, or a page and an area in a document. | G1: no value without a source |
| In-region | AI processing stays in the client's region. EU data stays in the EU. India data stays in India. There is no fallback to another region. | G7: region stays fixed |
| Private | We never train models on a client's code or data. One client's data never helps another client. | G6: tenant isolation |
| Human-approved | No change, release or decision happens without a human approval. | G13: human approval before any external action |

**Three capabilities:**

1. **Legacy Modernisation.** Traceable reverse engineering, a modernisation assessment and pilot delivery.
2. **AI Product Delivery.** Fractional AI product leadership, from use case to launch.
3. **Exaktiv Product Data (early access).** Source-linked product data from supplier datasheets.

**Voice rules:**

- Peer, not guru. Plain and specific.
- Open with a claim. Back it with a fact. Close with what the reader gets.
- Numbers and nouns, not adjectives. No hype words ("revolutionary", "cutting-edge", "seamless").
- British spelling. No em dashes. No emoji.
- Short sentences. One idea per sentence.

## 5. Sitemap and page requirements

The site has 10 pages at launch. The legal notice is added in phase 2. Two utility pages, `/contact/thanks/` and `/contact/problem/`, are states of the contact form: always noindex, not in the sitemap, not counted here (EXW1-ui).

**Main navigation:** Capabilities (menu with 3 items) · How we work · Security · Team · Contact (button).
**Footer:** Privacy notice · Security contact (security.txt) · © 2026 Exaktiv. No company name in the footer (EXW3, 19 Nov 2026). Phase 2: Legal notice.

| Page | Purpose | Must contain | Primary call to action |
| --- | --- | --- | --- |
| Home | Explain Exaktiv in 10 seconds | Core claim, 3 capability cards, 4 proof pillars, a short "how we work" strip, team experience in one line | Talk to us |
| Legacy Modernisation | Win modernisation leads | The problem, our method (Assess, Pilot, Modernise), deliverables of each stage, a sample traceable finding, "Why now" EU rules box | Request an assessment |
| AI Product Delivery | Win AI product leads | Typical problems, engagement models (sprint, fractional, build support), what the client gets | Book a call |
| Product Data (early access) | Collect interest for the product | What it does, who it is for, "early access" label, no claims of live customers | Join early access |
| How we work | Show the method and the guardrails | 4 pillars in plain words, the engagement steps, what we need from the client | Talk to us |
| Security and data handling | Answer the security reviewer | Region table, model use, retention, access, no training, NDA and DPA on request, incident contact | Ask for our security pack |
| Team | Show experience without names | Combined experience, domains, skills, anonymous examples of past work | Talk to us |
| Contact | Capture leads | Form (section 7), reply-time promise, email address | Send |
| Privacy notice | Meet GDPR transparency duties | Privacy notice in section 8.3 | None |
| 404 | Recover lost visitors | Short message, links to Home and Contact | Go to Home |

**Acceptance criteria for every page:**

- [ ] One H1 that states the page's point.
- [ ] A call to action above the fold on desktop and on mobile.
- [ ] No personal, employer or client names.
- [ ] Every factual claim is in the claims register (section 6) with status "approved".
- [ ] The page passes the non-functional checks in section 10.

## 6. Claims register

A claim goes on the site only when its evidence exists. This is our own G1 rule applied to marketing. A security reviewer will test these claims, so each one must be true on launch day.

**Approved claims (each needs its evidence before launch):**

| Claim | Where it appears | Evidence needed | Status |
| --- | --- | --- | --- |
| 26+ years of combined experience | Home, Team | Both CVs | Ready |
| AI processing stays in your region | Home, Security, How we work | Internal register of the AI model endpoints we use per region, with provider terms | To confirm |
| We never train models on your code or data | Security, How we work | Provider terms with no-training and no-retention settings, plus our written policy | To confirm |
| Every finding links to its source | Home, Legacy Modernisation | A demo output from our legacy analyser that shows file and line links | To confirm |
| No change without human approval | How we work | Written engagement process | To write |
| NDA and DPA on request | Security | NDA template and DPA template with standard contractual clauses | To write |
| Reply within 1 business day | Contact | Inbox routine | Ready |

**Banned claims (never on the site):**

- "GDPR compliant", "GDPR certified" or "EU AI Act compliant". Use "built on GDPR principles" only after the privacy notice and DPA exist.
- Any certification we do not hold (ISO 27001, SOC 2, TISAX).
- "Trusted by", client logos, client counts or testimonials.
- "100% accurate", "fully automated modernisation" or "no human needed".
- "EU company", "German company" or any office address we do not have.
- Product Data as "live" or "in production".

## 7. Contact form

The contact form goes live at launch. Valyrian Tech Pvt Ltd is the controller of the data, and the privacy notice names the company only. The form collects only what we need to reply, stores submissions in the EU and sets no cookies. A mailto link to the domain address stays as a second route.

**Fields:**

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| Name | Text | Yes | 2 to 100 characters |
| Work email | Email | Yes | Valid email format |
| Company | Text | Yes | 2 to 150 characters |
| Role | Text | No | Up to 100 characters |
| Topic | Dropdown | Yes | Legacy modernisation, AI product delivery, Product data early access, Partnership, Other |
| Where is your data? | Dropdown | No | EU or UK, India, Other. This tells us which region to set up. |
| Message | Long text | Yes | 20 to 2,000 characters |

**Functional requirements:**

1. Validate each field in the browser and again on the server. Show the error next to the field.
2. Under the submit button, show: "We use your details only to reply to you. See our privacy notice." with a link. No marketing consent box at launch, because we send no marketing.
3. Block spam with a hidden honeypot field, a minimum fill time and a rate limit per IP address. Do not use a captcha from a provider that sets cookies or sends data outside the EU.
4. On success, show a confirmation message and send an automatic reply to the sender: what happens next and when.
5. Send each submission to the team inbox. Store it in the EU region only.
6. Delete submissions after 6 months, unless they lead to a contract.
7. Log no message content in application logs. Mask email addresses in logs (engine rule G11).

**Acceptance criteria:**

- [ ] Given a valid submission, the sender sees a confirmation, gets an automatic reply, and the team inbox gets the message within 1 minute.
- [ ] Given a missing required field, the form shows the error and sends nothing.
- [ ] Given a filled honeypot field, the server drops the submission without an error message.
- [ ] Given 6 submissions from one IP address in 10 minutes, the 6th is refused.
- [ ] A browser check shows no cookies and no requests to third-party domains on the contact page.

## 8. Security, privacy and in-region AI processing

The site applies the EU standard to every visitor, worldwide. This is simpler than one rule per country, and it shows buyers how we treat their data.

### 8.1 In-region AI processing (the promise on the Security page)

| Client data region | Files and code stored in | AI models run in | Fallback to another region |
| --- | --- | --- | --- |
| EU or UK | EU region | EU-region model endpoints only | Never. The task stops and goes to a human. |
| India | India region | India-region model endpoints only | Never |
| Other | Agreed in the contract | Agreed in the contract | Never |

Other rules on the Security page:

- We use model providers only on terms that exclude training on client data and limit retention.
- We work inside the client's own environment when the client asks.
- Access to client code is limited to the named delivery team and is logged.
- NDA before access. DPA with standard contractual clauses on request.
- We name the regions and provider types on the page. We list the exact providers in the security pack, which we send on request.

### 8.2 Website security

- Hosting in an EU region, within the current limit of $10 per month per region. Server logs store truncated IP addresses only, and keep them for 14 days.
- HTTPS only, TLS 1.2 or later, HSTS.
- Security headers: Content-Security-Policy with no third-party sources, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, frame-ancestors none.
- Fonts and all assets hosted on our own domain. No external CDNs, font services or embeds.
- A security.txt file (RFC 9116) with a security contact address.
- Dependencies scanned before each deploy. Secrets never in the repository (engine rule G9).

### 8.3 Privacy notice: required content

The privacy notice names Valyrian Tech Pvt Ltd as the controller. It names no person.

1. Controller: Valyrian Tech Pvt Ltd, its registered address in India and a contact email on the domain.
2. What we collect: form data, and server logs with truncated IP addresses.
3. Purposes and legal bases: reply to an enquiry and steps before a contract (GDPR Art. 6(1)(b)); site security (Art. 6(1)(f)).
4. Recipients: the hosting provider and the email provider, each under a data processing agreement.
5. Transfers: the team reads enquiries in India, which has no EU adequacy decision. Basis: the visitor's own request before a contract (Art. 49(1)(b)), and standard contractual clauses with processors.
6. Retention: form data 6 months; server logs 14 days.
7. Rights: access, correction, erasure, restriction, objection, portability, and the right to complain to a data protection authority.
8. No cookies, no tracking, no automated decisions.
9. India: the substantive DPDP duties apply from 13 May 2027 ([source](https://amlegals.com/?p=57401)). Write the notice so that it also meets them.

A data protection lawyer reviews the notice before launch.

**Note on the phase 2 legal notice:** for a company, the legal notice must name its legal form and its authorised representatives ([source](https://www.ihk.de/rhein-neckar/recht/wirtschaftsrecht/internet/informationspflichten-internet-938654)). So the directors' names appear there. Plan the timing of phase 2 with this in mind.

## 9. Design requirements

> **Superseded on 18 Nov 2026.** The Exaktiv brand package in `brand/` replaces the brand rules in this section (v4 tokens, General Sans, Martian Mono, pill buttons, offset shadows). Use `brand/README.md` and `brand/guidelines/index.html`. The constraints (no names, no stock people, no maps) still apply.

Exaktiv gets its own identity, built on the Ved Design System v4 tokens. It does not use the Winky V mark or a "by Ved." line, because those identify a founder (constraint 1).

**Brand rules:**

- **Wordmark:** "Exaktiv" in General Sans 700. No other logo at launch.
- **Colours:** Chalk #FBF7EF page, Ink #101A33 text and outlines, Kirana #0E7C7B as the main accent, Lemon #FFE14D only for primary buttons (Ink text on Lemon). Never Lemon text on Chalk. Night #0E1530 for dark mode, where accent text turns Lemon.
- **Type:** General Sans 400 and 500 for body and UI. Newsreader italic only for one word or phrase of emphasis in a headline. Martian Mono for code, file paths, line numbers and figures.
- **Shapes:** 2px Ink borders, one hard Ink offset shadow (4px on buttons, 6px on cards), never blurred. Pill buttons. Card radius 16px.
- **Tone:** more sober than the personal brand. Use Lemon sparingly. Do not use verdict stickers, coin ratings or price tags.
- **Modes:** light by default. Dark mode follows the system setting.

**Signature visual: the traceable finding.** A card that shows a short legacy code excerpt on one side and a plain-language specification line on the other. The specification line ends with its source in Martian Mono, for example `billing/Invoice.java:142`. Use invented, generic code only. Never real client code.

**Imagery rules:** no stock photos of people, no AI-generated faces, no world maps or pins that suggest offices. Use diagrams for the region table and the engagement steps.

**Design deliverables:**

1. Desktop (1440px) and mobile (390px) layouts for every page in section 5.
2. Component sheet: header, footer, buttons, capability card, pillar card, traceable finding card, region table, form fields with error states, cookie-free notice line.
3. A token file that maps to the v4 tokens. No hard-coded colour values in components.

**Note:** resolved on 18 Nov 2026 (open item O1). The repository rules now point to the Exaktiv brand package in `brand/`.

## 10. Non-functional requirements

| Area | Requirement | How to check |
| --- | --- | --- |
| Performance | Largest Contentful Paint under 2.5 s on a mid-range phone over 4G. Page weight under 1 MB. | Lighthouse mobile run |
| Quality score | Lighthouse 90 or more for performance, accessibility, best practices and SEO | Lighthouse report per page |
| Accessibility | WCAG 2.2 level AA: contrast, keyboard use, visible focus, form labels, alt text | Automated check plus a manual keyboard test |
| Build | Static site. The only server-side part is the form endpoint. | Code review |
| Browsers | Latest 2 versions of Chrome, Edge, Safari and Firefox, on desktop and mobile | Manual test |
| SEO | Unique title and description per page, Open Graph image, sitemap.xml, robots.txt, canonical URLs, schema.org Organization with name, url and logo only: no legalName and no Person data (EXW3, 19 Nov 2026) | SEO check |
| AI search | Clean semantic HTML, one clear H1 per page, an llms.txt file that summarises the capabilities | Manual check |
| Language | lang="en-GB" on every page | Code review |
| Hosting | EU region, $10 per month or less | Provider invoice |
| Domain and email | A neutral, global domain (not a country domain). Email on the same domain with SPF, DKIM and DMARC. | DNS check |
| Staging | Password protected and noindex until launch | Request without the password returns 401 |

## 11. Launch plan, risks and open decisions

The site launches when every item in the definition of done is ticked. Close decisions D1 to D6 first.

**Launch steps:**

1. Close decisions D1 to D6.
2. Approve the copy deck (section 12).
3. Design: desktop and mobile layouts, component sheet, token file.
4. Build on a password-protected staging site.
5. Claims check: every claim in section 6 is "Ready".
6. Legal check of the privacy notice.
7. Launch.
8. Phase 2, when the first contract is close: add the legal notice for Valyrian Tech Pvt Ltd and cookie-free analytics hosted in the EU.

**Definition of done:**

- [ ] All 10 pages built and approved on staging.
- [ ] All approved claims have evidence. No banned claim appears.
- [ ] Contact form passes all acceptance criteria in section 7.
- [ ] Browser check: zero cookies and zero third-party requests on every page.
- [ ] Security headers and security.txt in place.
- [ ] Lighthouse 90+ and WCAG 2.2 AA checks pass.
- [ ] Privacy notice reviewed by a lawyer.
- [ ] No personal, employer or client names anywhere, including image file names and page metadata.

**Risks:**

| Risk | Effect | Mitigation |
| --- | --- | --- |
| The site describes services that overlap with a team member's current employer | Employment dispute | Finish the employment contract check before launch. The email and any contract will name the sender, whatever the site shows. |
| No legal notice while a commercial site serves EU buyers | Warning letters or fines (up to €50,000 in Germany) ([source](https://www.ihk.de/rhein-neckar/recht/wirtschaftsrecht/internet/informationspflichten-internet-938654)) | Global framing with no country targeting. Add the legal notice before the first contract. Ask a lawyer to confirm the timing. |
| GDPR requires the privacy notice to name the controller | The privacy notice is incomplete | Resolved: the notice names Valyrian Tech Pvt Ltd in one sentence, with its registered address (D3) |
| A claim goes live before its evidence exists | Loss of trust at the first security review | Claims register gate (section 6) |
| Spam through the form | Wasted time, noise in the inbox | Honeypot, minimum fill time, rate limit |

**Open decisions:**

| ID | Decision | Options | Recommendation |
| --- | --- | --- | --- |
| D1 | Domain | A neutral global domain such as .com, .ai or .io | A .com if available. Avoid .de. |
| D2 | Brand | Exaktiv identity on v4 tokens, or another identity | Exaktiv identity on v4 tokens, with no Winky V and no "by Ved." |
| D3 | Controller identity in the privacy notice | Decided: Valyrian Tech Pvt Ltd is the controller. | Name the company only. No personal name on the site. Confirm with a lawyer. |
| D4 | Form back end | EU-hosted form service, or our own endpoint on the EU server | Our own endpoint. It keeps the "no third parties" promise. |
| D5 | Hosting | Hetzner (Germany or Finland), or another EU host | Hetzner. It matches the Exaktiv EU hosting decision. |
| D6 | Email provider | An EU-based mail provider, or a global one under a DPA | An EU-based provider |

**Open item O1:** ✅ Done 18 Nov 2026. The repository rules now point to `brand/`.

## 12. Appendix: copy deck

This is draft copy for design. Final copy needs approval (launch step 2).

### Home

- **H1:** AI you can audit.
- **Subhead:** We modernise legacy software and ship AI products. Every finding links to its source. Your data stays in your region.
- **Button:** Talk to us
- **Capability cards:**
  - *Legacy Modernisation:* Turn code that nobody understands into a specification you can check, line by line. Then modernise in safe stages.
  - *AI Product Delivery:* Go from an AI idea to a feature your customers use, with senior product leadership when you need it.
  - *Exaktiv Product Data (early access):* Structured product data from supplier datasheets. Every value links to its page.
- **Pillars:** Traceable · In-region · Private · Human-approved (text from section 4)
- **Team line:** 26+ years of combined experience in product leadership and enterprise architecture.

### Legacy Modernisation

- **H1:** Legacy code, *explained* before it is changed.
- **Problem:** The people who wrote the code have left. The documentation is old. Every change is a risk.
- **Method:**
  1. *Assess (3 to 4 weeks, fixed price):* AI-assisted reverse engineering into a traceable specification, a system map, a risk register, target architecture options and a roadmap.
  2. *Pilot:* modernise one module end to end, with tests that prove the old and the new behave the same.
  3. *Modernise:* scale the method, module by module, with your team.
- **Sample finding (card):** "An invoice is cancelled only when no payment is booked against it." Source: `billing/Invoice.java:142`
- **Button:** Request an assessment

**"Why now" box (EU rules for software vendors):**

- Cyber Resilience Act: reporting of actively exploited vulnerabilities applies since 11 September 2026, also for products already on the market. Full duties, including the SBOM, apply from 11 December 2027 ([source](https://www.noze.it/en/insights/cyber-resilience-act-sbom/)).
- EU Data Act: cloud switching rules apply since 12 September 2025. Switching and egress charges are banned from 12 January 2027 ([source](https://www.cloudmagazin.com/en/2026/07/15/eu-data-act-makes-cloud-portability-mandatory/)).
- NIS2: now national law in member states. In Germany since 6 December 2025 ([source](https://www.secfix.com/post/germanys-new-nis2-cybersecurity-law)). Customers pass its supply-chain duties on to their software suppliers.
- EU AI Act: high-risk duties for stand-alone systems apply from 2 December 2027, and for AI in regulated products from 2 August 2028 ([source](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-)).
- Footnote on the page: "This is general information, not legal advice."

### AI Product Delivery

- **H1:** From AI idea to a feature *customers use*.
- **Models:** a 2-week AI opportunity sprint, fractional AI product leadership, and build support.
- **Button:** Book a call

### Security and data handling

- **H1:** Your code stays where you say.
- **Body:** The region table and rules from section 8.1.
- **Button:** Ask for our security pack

### Team

- **H1:** Senior people. *No* hand-offs.
- **Body:** 26+ years of combined experience across BFSI, insurance, retail and e-commerce.
- **Past work (anonymous):** modernised lending and insurance platforms for a large life insurer; designed workflow architecture for a global retailer's item data platform; led product delivery for advertising products on a large e-commerce marketplace; built AI agents for legacy code analysis.
- **Skills:** product discovery and delivery governance; Java, Spring Boot, Kotlin, Temporal, Kafka, PostgreSQL and distributed systems; LangChain, LangGraph and agentic systems; threat modelling, OWASP Top 10 and post-quantum cryptography migration.
- **Check before launch:** confirm that no description can identify a client.

### Contact

- **H1:** Tell us what you need.
- **Body:** We reply within 1 business day.

## Sources

- [CRA timeline and SBOM (noze)](https://www.noze.it/en/insights/cyber-resilience-act-sbom/)
- [EU Data Act switching fees (cloudmagazin)](https://www.cloudmagazin.com/en/2026/07/15/eu-data-act-makes-cloud-portability-mandatory/)
- [Germany NIS2 law in force (Secfix)](https://www.secfix.com/post/germanys-new-nis2-cybersecurity-law)
- [EU AI Act Omnibus agreement (Gibson Dunn)](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-)
- [Legal notice duties and fines (IHK Rhein-Neckar)](https://www.ihk.de/rhein-neckar/recht/wirtschaftsrecht/internet/informationspflichten-internet-938654)
- [DPDP Rules timeline (AMLEGALS)](https://amlegals.com/?p=57401)
