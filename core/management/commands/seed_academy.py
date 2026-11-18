"""
Load the academy's starter content (tracks, syllabus, stats, benefits, team, FAQs).

    python manage.py seed_academy

Safe to re-run: records are matched by slug/title and updated in place.
Images you upload in the admin are never overwritten.
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import FAQ, Benefit, Stat, SyllabusWeek, TeamMember, Track

STATS = [
    ("Students Reached", 8000, "+", "fa-solid fa-user-graduate"),
    ("Graduate Employment Rate", 67, "%", "fa-solid fa-briefcase"),
    ("Countries Represented (incl. North America)", 40, "+", "fa-solid fa-globe"),
    ("Target: Individuals across Africa in Tech", 100000, "+", "fa-solid fa-bullseye"),
]

BENEFITS = [
    ("Free Tech Tuition", "Valued at $213 completely accessible for committed learners."),
    ("Structured Pathways", "Curated learning roadmaps designed for rapid skill acquisition."),
    ("Vibrant Community", "Network with thousands of tech enthusiasts across the globe."),
    ("Student Portals", "Designated learning dashboards for seamless tracking."),
    ("Certificate of Completion", "Awarded upon successful course requirement completion."),
    ("Excellence Recognition", "Special certificates awarded to top-performing students."),
    ("LinkedIn Optimization", "Advanced practical class to profile & position yourself for recruiters."),
    ("Live & Recorded Sessions", "Weekly interactive classes coupled with self-paced resources."),
    ("AMA Sessions", 'Direct "Ask Me Anything" mentorship opportunities with experts.'),
    ("Immediate Internships", "Direct internship offers from our partner institutions."),
    ("Earn while you Learn", "Direct access to free elite money making courses, information and resources "
                             "including affiliate marketing and YouTube optimisation."),
]

TEAM = [
    {
        "name": "Moshood Lawal",
        "role_heading": "FOUNDER & CEO",
        "title": "Founder & CEO, MS. Virtual Academy",
        "bio": "A global Leader focused on lowering the barriers to high-tier technical mastery. Believing that "
               "digital education must be directly practical, modern, and globally validated, building MS. Virtual "
               "Academy to empower individuals and students worldwide with real-world skills capable of driving "
               "instantaneous career breakthrough.",
        "photo": "765341.jpg",
    },
    {
        "name": "Yisa Sultan",
        "role_heading": "CO-FOUNDER & OPERATIONS MANAGER",
        "title": "Co-founder & Operations Manager, MS. Virtual Academy",
        "bio": "A young prompt and AI engineer driven by a commitment to efficiency, innovation and continuous "
               "learning. Providing the platform where lives will be transformed and engaged with.",
        "photo": "885855.jpg",
    },
]

GENERAL_FAQS = [
    ("Is the training really free?",
     "Yes. Tuition (valued at $213) is free for committed learners who are admitted into a cohort."),
    ("How long does each track take?",
     "Each track runs for 6 weeks of live and recorded sessions, followed by projects and practical sessions."),
    ("Do I need prior experience?",
     "No. Our tracks are designed to take you from foundational principles to career-ready skills. "
     "Some tracks list recommended prerequisites on their page."),
    ("How are applicants selected?",
     "Our admissions team reviews every application. Shortlisted applicants are contacted by email or phone "
     "with next steps."),
    ("Will I get a certificate?",
     "Yes. A Certificate of Completion is awarded once you complete the course requirements, and top-performing "
     "students receive special Excellence Recognition certificates."),
]

WRAP = "Projects and practical sessions"

TRACKS = [
    {
        "title": "Cybersecurity",
        "icon": "fa-solid fa-shield-halved",
        "tagline": "Defend systems. Secure the future.",
        "short_description": "Learn to protect networks, systems and data from modern threats with hands-on "
                             "labs in networking, penetration testing and SIEM.",
        "overview": "Cybersecurity is one of the fastest-growing fields in tech, with organisations worldwide "
                    "competing for skilled defenders. This track takes you from networking and Linux fundamentals "
                    "to threat analysis, vulnerability assessment and security operations.\n\nYou will practise in "
                    "realistic lab environments, learn how attackers think, and finish with a defensive audit "
                    "capstone that demonstrates job-ready skills.",
        "outcomes": "Explain the OSI and TCP/IP models and how traffic flows across networks\n"
                    "Harden Linux systems against common attacks\n"
                    "Perform vulnerability assessments and basic penetration tests\n"
                    "Configure Identity & Access Management controls\n"
                    "Monitor and investigate alerts in a SIEM\n"
                    "Produce a professional security audit report",
        "tools": "Kali Linux\nWireshark\nNmap\nBurp Suite\nMetasploit\nSplunk\nTryHackMe",
        "prerequisites": "A laptop (8GB RAM recommended) and stable internet\nBasic computer literacy\n"
                         "Curiosity about how systems work and break",
        "career_paths": "SOC Analyst\nCybersecurity Analyst\nPenetration Tester (Junior)\nIAM Analyst\n"
                        "Security Consultant",
        "weeks": [
            ("Foundations of Networking, TCP/IP Models, and Linux Security Baselines",
             "Build the networking and operating-system foundation every security professional needs.",
             "OSI vs TCP/IP models\nIP addressing, ports & protocols\nLinux command line essentials\n"
             "File permissions & user management\nSecurity baselines and hardening",
             "Harden a Linux virtual machine and document the changes"),
            ("Threat Landscapes, Vulnerability Assessments, and Penetration Testing Frameworks",
             "Understand how attackers operate and how to find weaknesses before they do.",
             "Threat actors & attack vectors\nCVEs and vulnerability scoring (CVSS)\nScanning with Nmap\n"
             "Penetration testing phases & frameworks\nWeb vulnerabilities (OWASP Top 10)",
             "Vulnerability assessment report on a lab target"),
            ("Identity & Access Management (IAM) and Security Information Event Management (SIEM)",
             "Control who has access to what, and detect when something goes wrong.",
             "Authentication vs authorisation\nMFA, SSO and least privilege\nLog sources and log analysis\n"
             "SIEM dashboards and alert triage\nIncident response basics",
             "Investigate and write up a simulated security incident"),
            ("Capstone Project: Defensive Auditing & Global Certification Examination",
             "Bring everything together in a full defensive audit.",
             "Audit planning & scope\nControl testing\nRisk rating & remediation plans\nCertification exam preparation",
             "Complete a defensive security audit of a simulated organisation"),
            (WRAP, "Guided projects to deepen practical skills.",
             "Capture-the-flag (CTF) challenges\nPeer review sessions\nPortfolio write-ups", "CTF portfolio entry"),
            (WRAP, "Final practical sessions and career preparation.",
             "Mock interviews\nCV & LinkedIn positioning for security roles\nFinal project presentations",
             "Present your capstone to the cohort"),
        ],
        "faqs": [("Do I need a powerful laptop?",
                  "A laptop with at least 8GB RAM is recommended so you can run virtual machines for labs.")],
    },
    {
        "title": "Data Analysis",
        "icon": "fa-solid fa-chart-pie",
        "tagline": "Turn raw data into decisions.",
        "short_description": "Master Excel, SQL and Power BI/Tableau to clean, analyse and visualise data, "
                             "then present insights like a professional analyst.",
        "overview": "Every organisation runs on data, and analysts turn it into decisions. In this track you will "
                    "learn the analyst's core toolkit, from spreadsheets and SQL to interactive business "
                    "intelligence dashboards.\n\nThe track ends with a capstone where you present analytical "
                    "insights to simulated corporate stakeholders, just as you would on the job.",
        "outcomes": "Clean and transform messy datasets in Excel\nWrite SQL queries to filter, join and aggregate data\n"
                    "Build interactive dashboards in Power BI or Tableau\nChoose the right chart for each question\n"
                    "Communicate insights clearly to non-technical stakeholders",
        "tools": "Microsoft Excel\nGoogle Sheets\nSQL (PostgreSQL / MySQL)\nPower BI\nTableau",
        "prerequisites": "A laptop and stable internet\nBasic arithmetic and comfort with numbers",
        "career_paths": "Data Analyst\nBusiness Intelligence Analyst\nReporting Analyst\nOperations Analyst",
        "weeks": [
            ("Advanced Microsoft Excel data cleaning, parsing, and logical functions",
             "Get fast and accurate with the world's most used analytics tool.",
             "Data cleaning techniques\nText parsing functions\nIF, IFS, XLOOKUP and logical functions\n"
             "PivotTables and PivotCharts",
             "Clean and summarise a real-world sales dataset"),
            ("Structured Query Language (SQL) for relational database manipulation and querying",
             "Query databases directly to answer business questions.",
             "SELECT, WHERE, ORDER BY\nJOINs across tables\nGROUP BY and aggregates\nSubqueries and CTEs",
             "Answer 15 business questions with SQL"),
            ("Business Intelligence dashboards with Power BI or Tableau",
             "Turn analysis into interactive, decision-ready dashboards.",
             "Connecting data sources\nData modelling basics\nDesigning effective visuals\nFilters, slicers & drill-downs",
             "Build an executive KPI dashboard"),
            ("Practical Capstone: Presenting analytical insights to simulated corporate stakeholders",
             "Deliver an end-to-end analysis and present your recommendations.",
             "Framing the business problem\nStorytelling with data\nPresentation & Q&A skills",
             "Capstone presentation to stakeholders"),
            (WRAP, "Guided projects across new datasets.",
             "Industry case studies\nPeer reviews\nPortfolio building", "Second portfolio project"),
            (WRAP, "Career preparation and final showcase.",
             "Analyst interview practice\nCV & LinkedIn optimisation\nFinal showcase", "Publish your portfolio"),
        ],
        "faqs": [("Power BI or Tableau?",
                  "You can choose either. Concepts are taught so they transfer between both tools.")],
    },
    {
        "title": "Digital Marketing",
        "icon": "fa-solid fa-bullhorn",
        "tagline": "Grow brands with data-driven marketing.",
        "short_description": "Learn copywriting, SEO, paid ads and growth analytics to plan and launch "
                             "campaigns that deliver measurable results.",
        "overview": "Businesses everywhere need marketers who can attract, convert and retain customers online. "
                    "This track covers the full digital marketing funnel, from persuasive copy and brand systems "
                    "to SEO, paid advertising and attribution.\n\nYou will finish by launching and analysing a "
                    "campaign against strict key metrics.",
        "outcomes": "Write direct-response copy that converts\nBuild SEO-friendly content funnels\n"
                    "Plan and run Google and Meta ad campaigns\nTrack performance with analytics and attribution\n"
                    "Report campaign results with clear KPIs",
        "tools": "Google Ads\nMeta Ads Manager\nGoogle Analytics 4\nGoogle Search Console\nCanva\nMailchimp",
        "prerequisites": "A laptop or smartphone with internet\nGood written communication",
        "career_paths": "Digital Marketer\nSocial Media Manager\nSEO Specialist\nPerformance Marketer\nContent Strategist",
        "weeks": [
            ("Direct-Response Copywriting, Brand Systems, and Audience Analytics",
             "Understand your audience and craft messages that move them.",
             "Customer personas\nCopywriting frameworks (AIDA, PAS)\nBrand voice & positioning\nAudience research tools",
             "Write a landing page and ad copy set"),
            ("Search Engine Optimization (SEO) architectures and Content Funnel Design",
             "Get found on search engines and guide visitors to convert.",
             "Keyword research\nOn-page & technical SEO\nContent funnels (TOFU/MOFU/BOFU)\nLink building basics",
             "SEO audit and content plan"),
            ("Paid Advertising frameworks across Google Ads, Meta Ads, and Data Attribution",
             "Run profitable paid campaigns and know what's working.",
             "Campaign structures\nTargeting & bidding\nCreative testing\nAttribution models",
             "Draft a paid media plan with budget"),
            ("Campaign Launch & Growth Hacking analysis under strict key metrics",
             "Launch, measure and iterate on a live campaign.",
             "Growth experiments\nKPI dashboards\nA/B testing\nReporting results",
             "Campaign performance report"),
            (WRAP, "Hands-on client-style projects.",
             "Social media strategy\nEmail marketing\nPeer reviews", "Client marketing proposal"),
            (WRAP, "Career preparation and final showcase.",
             "Freelancing & job search\nPortfolio presentation\nLinkedIn personal branding", "Final portfolio"),
        ],
        "faqs": [("Do I need money for ads?",
                  "No. You will learn with demo accounts and simulations; running real ads is optional.")],
    },
    {
        "title": "Digital Services",
        "icon": "fa-solid fa-laptop-code",
        "tagline": "Build a global digital services business.",
        "short_description": "Learn no-code automation, freelancing, consulting and agency-building skills "
                             "to deliver digital services to clients worldwide.",
        "overview": "Small and medium businesses worldwide need help going digital. This track teaches you how to "
                    "deliver those services profitably: building with no-code tools, writing winning proposals, "
                    "consulting on digital transformation and launching your own agency.\n\nBy the end you will "
                    "have a portfolio and a plan for landing remote clients.",
        "outcomes": "Build websites and automations with no-code tools\nWrite proposals and contracts that win clients\n"
                    "Advise SMEs on digital transformation\nPackage and price your services\n"
                    "Find and close remote work opportunities",
        "tools": "WordPress\nWebflow\nZapier\nMake (Integromat)\nNotion\nUpwork & Fiverr",
        "prerequisites": "A laptop and stable internet\nBasic computer literacy",
        "career_paths": "Freelancer\nNo-Code Developer\nDigital Transformation Consultant\nAgency Founder\n"
                        "Virtual Assistant",
        "weeks": [
            ("No-Code Web Automation, CMS platforms, and API integration",
             "Build real websites and workflows without writing code.",
             "CMS platforms (WordPress, Webflow)\nWorkflow automation with Zapier/Make\nWhat APIs are and how to use them",
             "Automate a business workflow end to end"),
            ("Technical Freelancing models, corporate proposal drafting, and contract creation",
             "Turn your skills into paid client work.",
             "Freelance business models\nWriting winning proposals\nContracts, scope & pricing",
             "Proposal and contract for a mock client"),
            ("Digital Transformation consulting methods for small and medium enterprises",
             "Help businesses modernise their operations.",
             "Assessing digital maturity\nRecommending tools & processes\nChange management basics",
             "Digital transformation plan for an SME"),
            ("Launching your Global Agency portfolio and remote work acquisition strategies",
             "Package your services and attract international clients.",
             "Portfolio and case studies\nOutreach & lead generation\nFreelance platforms",
             "Launch your agency portfolio"),
            (WRAP, "Client simulation projects.", "Client discovery calls\nDelivery workflows\nPeer reviews",
             "Deliver a client project"),
            (WRAP, "Final showcase and career preparation.", "Pitch practice\nPricing strategy\nFinal presentations",
             "Pitch your agency"),
        ],
        "faqs": [],
    },
    {
        "title": "Frontend Development",
        "icon": "fa-solid fa-code",
        "tagline": "Build beautiful, responsive web experiences.",
        "short_description": "Go from HTML and CSS to modern JavaScript, APIs and deployment by building and "
                             "shipping a production-ready responsive web app.",
        "overview": "Frontend developers build everything users see and interact with on the web. This track covers "
                    "semantic HTML, modern CSS layouts, JavaScript, asynchronous programming and working with live "
                    "APIs, plus the version control and tooling professionals use every day.\n\nYou will finish by "
                    "engineering and deploying a production-ready responsive web app.",
        "outcomes": "Write semantic, accessible HTML5\nBuild responsive layouts with Flexbox and CSS Grid\n"
                    "Program interactive features with JavaScript and the DOM\nFetch and display data from live APIs\n"
                    "Use Git/GitHub and deploy apps to the web",
        "tools": "HTML5\nCSS3\nJavaScript (ES6+)\nGit & GitHub\nVS Code\nNetlify",
        "prerequisites": "A laptop and stable internet\nNo prior coding experience required",
        "career_paths": "Frontend Developer\nWeb Developer\nUI Engineer\nFreelance Web Designer",
        "weeks": [
            ("Web Architecture, Semantic HTML5 Structures, and Accessibility (a11y) Standards", "", "", ""),
            ("Modern CSS3 Fundamentals, Flexbox Layouts, CSS Grid, and Mobile-First Responsive Systems", "", "", ""),
            ("JavaScript Essentials: Variables, Functions, DOM Manipulation, and Event Handlers", "", "", ""),
            ("Advanced JS: Asynchronous Logic, Promises, Fetch API, and Working with Live External APIs", "", "", ""),
            ("Version Control with Git/GitHub, Build Tools, and Modern UI Component Framework Basics", "", "", ""),
            ("Practical Capstone: Engineering & Deploying a Production-Ready Responsive Web App on Netlify", "", "",
             "Deploy your capstone web app"),
        ],
        "faqs": [],
    },
    {
        "title": "Backend Development",
        "icon": "fa-solid fa-server",
        "tagline": "Power applications from the server side.",
        "short_description": "Design REST APIs, model SQL and NoSQL databases, implement secure authentication "
                             "and deploy a production API.",
        "overview": "Backend developers build the servers, databases and APIs that power modern applications. This "
                    "track teaches backend architecture with Node.js and Express, REST API design, relational and "
                    "NoSQL databases, and secure authentication.\n\nYou will finish by hardening and deploying a "
                    "production REST API.",
        "outcomes": "Explain client-server architecture and HTTP\nBuild RESTful APIs with Express.js\n"
                    "Model data in PostgreSQL/MySQL and MongoDB\nImplement JWT authentication and password hashing\n"
                    "Secure and deploy an API to production",
        "tools": "Node.js\nExpress.js\nPostgreSQL / MySQL\nMongoDB & Mongoose\nPostman\nGit & GitHub",
        "prerequisites": "A laptop and stable internet\nBasic JavaScript knowledge recommended",
        "career_paths": "Backend Developer\nAPI Developer\nFull-Stack Developer\nSoftware Engineer",
        "weeks": [
            ("Introduction to Backend Architecture, Node.js Environment setup, and Express.js Core Concepts", "", "", ""),
            ("RESTful API Design Principles, Route Handling, Middleware Engineering, and Error Management", "", "", ""),
            ("Database Fundamentals: SQL & Relational Schema Modeling (PostgreSQL/MySQL Basics)", "", "", ""),
            ("NoSQL Solutions (MongoDB) & Object-Data Modeling (ODM) with Mongoose", "", "", ""),
            ("User Authentication Systems: JWT (JSON Web Tokens), Password Hashing (bcrypt), and Session Security",
             "", "", ""),
            ("Hands-On Capstone: Architecture, Security Hardening, and Deployment of a Production REST API", "", "",
             "Deploy your production REST API"),
        ],
        "faqs": [],
    },
    {
        "title": "Product Design",
        "icon": "fa-solid fa-pen-ruler",
        "tagline": "Design products people love to use.",
        "short_description": "Learn UX research, wireframing, Figma, UI systems and prototyping to design an "
                             "end-to-end mobile app case study.",
        "overview": "Product designers make technology useful and delightful. This track covers the complete UX/UI "
                    "process, from user research and information architecture to high-fidelity interfaces, "
                    "design systems and interactive prototypes in Figma.\n\nYou will finish with a portfolio-ready "
                    "mobile app case study prepared for developer handoff.",
        "outcomes": "Run user research and build personas\nMap user flows and information architecture\n"
                    "Design wireframes and high-fidelity UI in Figma\nBuild reusable components and design tokens\n"
                    "Prototype and usability-test your designs",
        "tools": "Figma\nFigJam\nMiro\nMaze (usability testing)\nNotion",
        "prerequisites": "A laptop and stable internet\nNo prior design experience required",
        "career_paths": "Product Designer\nUX Designer\nUI Designer\nUX Researcher",
        "weeks": [
            ("Principles of User Experience (UX), User Research Methods, Personas, and Empathy Mapping", "", "", ""),
            ("Information Architecture, User Flows, Wireframing Concepts, and Low-Fidelity Sketching", "", "", ""),
            ("Master Tooling in Figma: Auto Layout, Design Tokens, Components, and Style Libraries", "", "", ""),
            ("High-Fidelity User Interface (UI) Systems, Visual Hierarchy, Typography, and Color Theory", "", "", ""),
            ("Interactive Micro-Animations, Advanced Figma Prototyping, and Usability Testing Frameworks", "", "", ""),
            ("Portfolio Capstone: Designing an End-to-End Mobile App Product Case Study ready for Handoff", "", "",
             "Publish your product design case study"),
        ],
        "faqs": [],
    },
    {
        "title": "Graphics Design",
        "icon": "fa-solid fa-palette",
        "tagline": "Communicate visually with impact.",
        "short_description": "Master composition, vector and raster tools, branding systems and marketing "
                             "visuals to build a professional design portfolio.",
        "overview": "Graphic designers shape how brands look and communicate. This track teaches visual "
                    "communication principles, vector and raster tools, corporate branding systems and marketing "
                    "design across digital and print.\n\nYou will finish by rebranding an enterprise brand and "
                    "building a professional Behance portfolio.",
        "outcomes": "Apply composition, balance and visual hierarchy\nDesign logos and vector graphics\n"
                    "Edit and composite photos professionally\nCreate brand guidelines with typography and colour rules\n"
                    "Produce social media, print and packaging designs",
        "tools": "Adobe Illustrator\nAdobe Photoshop\nFigma\nCanva\nBehance",
        "prerequisites": "A laptop and stable internet\nAn eye for detail and creativity",
        "career_paths": "Graphic Designer\nBrand Designer\nSocial Media Designer\nFreelance Designer",
        "weeks": [
            ("Foundations of Visual Communication, Graphic Composition, Balance, and Brand Aesthetics", "", "", ""),
            ("Vector Graphic Mastery: Curves, Paths, and Logo Design Systems in Adobe Illustrator / Figma", "", "", ""),
            ("Raster Manipulation, Photo Editing, Compositing, and Masking Techniques in Photoshop", "", "", ""),
            ("Corporate Branding Systems: Typography Rules, Color Palettes, and Brand Guideline Documentation",
             "", "", ""),
            ("Marketing Visuals: Social Media Assets, Billboard Ads, Print Media Formats, and Packaging Layouts",
             "", "", ""),
            ("Practical Capstone: Rebranding an Enterprise Brand and Building a Professional Behance Design Portfolio",
             "", "", "Publish your Behance portfolio"),
        ],
        "faqs": [],
    },
]


class Command(BaseCommand):
    help = "Seed the database with MS. Virtual Academy starter content."

    @transaction.atomic
    def handle(self, *args, **options):
        for i, (label, value, suffix, icon) in enumerate(STATS):
            Stat.objects.update_or_create(label=label, defaults={
                "value": value, "suffix": suffix, "icon": icon, "order": i})

        for i, (title, desc) in enumerate(BENEFITS):
            Benefit.objects.update_or_create(title=title, defaults={"description": desc, "order": i})

        for i, (q, a) in enumerate(GENERAL_FAQS):
            FAQ.objects.update_or_create(track=None, question=q, defaults={"answer": a, "order": i})

        image_dir = Path(settings.BASE_DIR) / "static" / "images"
        for i, data in enumerate(TEAM):
            data = dict(data)
            photo = data.pop("photo")
            member, _ = TeamMember.objects.update_or_create(name=data["name"], defaults={**data, "order": i})
            if not member.photo and (image_dir / photo).exists():
                with open(image_dir / photo, "rb") as fh:
                    member.photo.save(photo, File(fh), save=True)

        for i, data in enumerate(TRACKS):
            data = dict(data)
            weeks = data.pop("weeks")
            faqs = data.pop("faqs")
            track = Track.objects.filter(title=data["title"]).first() or Track(title=data["title"])
            for key, value in data.items():
                setattr(track, key, value)
            track.order = i
            track.save()

            for n, (title, summary, topics, deliverable) in enumerate(weeks, start=1):
                SyllabusWeek.objects.update_or_create(track=track, week_number=n, defaults={
                    "title": title, "summary": summary, "topics": topics, "deliverable": deliverable})
            for n, (q, a) in enumerate(faqs):
                FAQ.objects.update_or_create(track=track, question=q, defaults={"answer": a, "order": n})

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(TRACKS)} tracks, {len(STATS)} stats, {len(BENEFITS)} benefits, "
            f"{len(TEAM)} team members and {len(GENERAL_FAQS)} FAQs."))
