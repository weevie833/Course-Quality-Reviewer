"""
Ingests SHRM BASK 2026 Competency Framework into the database.

Structure:
  - 6 categories  = SHRM clusters / knowledge domains
  - 45 competencies = named sub-competency areas (e.g. 1.01.01 Navigating the Organization)

The description field contains the full proficiency indicator language for both
All HR Professionals and Advanced HR Professionals levels, enabling Claude to
match competency language to course assignments when answering questions like
"Which SHRM competencies most directly relate to the summative assignments in this course?"

No item links are inserted here — links will be added once course-assignment
mappings are determined.

Safe to re-run: drops and recreates only SHRM-prefixed category data.
"""

import sqlite3

DB_PATH = "data/program.db"

CATEGORIES = [
    ("SHRM-1", "Leadership Cluster"),
    ("SHRM-2", "Interpersonal Cluster"),
    ("SHRM-3", "Business Cluster"),
    ("SHRM-4", "People Knowledge Domain"),
    ("SHRM-5", "Organization Knowledge Domain"),
    ("SHRM-6", "Workplace Knowledge Domain"),
]

# (category_letter, code, name, description)
# description = full proficiency indicator text, both levels
COMPETENCIES = [

    # =========================================================
    # LEADERSHIP CLUSTER
    # =========================================================

    ("SHRM-1", "HRM-1.01.01", "Navigating the Organization",
     "All HR Professionals: Demonstrates an understanding of formal and informal work roles, "
     "leader goals and interests, and relationships among employees and executives. Facilitates "
     "communication and decision-making necessary to implement initiatives. Uses awareness and "
     "understanding of the organization's political environment and culture to implement HR "
     "initiatives. Uses an understanding of the organization's structure, processes, systems and "
     "policies to facilitate the successful implementation of HR initiatives. "
     "Advanced HR Professionals: Uses an understanding of complex relationships among "
     "organizational leaders to facilitate the design, implementation and maintenance of "
     "initiatives. Uses an understanding of the organization's political environment to develop "
     "and implement HR's strategic direction, implement needed changes, and resolve talent needs "
     "and issues. Uses an understanding of the complex relationships among the organization's "
     "formal and informal processes, systems and policies to facilitate the development and "
     "implementation of HR's strategic direction."),

    ("SHRM-1", "HRM-1.01.02", "Vision",
     "All HR Professionals: Embraces and supports the business unit's and/or organization's "
     "culture, values, mission and goals. Defines actionable goals for the development and "
     "implementation of HR programs, practices and policies that support the strategic vision of "
     "HR and the organization. Identifies opportunities to improve HR operations that better align "
     "with and support the strategic vision of HR and the organization. Supports the implementation "
     "of HR programs, practices and policies that uphold the strategic vision of HR and the "
     "organization. "
     "Advanced HR Professionals: Envisions the current and ideal future states of the HR function, "
     "organization and culture to identify gaps and areas for improvement. Develops the long-term "
     "strategic direction, vision and goals of HR and the organization to close the gap between "
     "the current and ideal states. Develops and socializes a broad plan to achieve the strategic "
     "direction, vision and goals of HR and the organization. Solicits feedback from "
     "executive-level stakeholders on strategic direction, vision and goals. Pivots HR strategy, "
     "approaches and/or programs in response to significant changes within and outside of the "
     "organization."),

    ("SHRM-1", "HRM-1.01.03", "Managing HR Initiatives",
     "All HR Professionals: Defines and elaborates on project requirements set by leadership. "
     "Sets and monitors project goals and progress milestones. Manages project budgets and "
     "resources. Identifies and develops solutions for overcoming obstacles to the successful "
     "completion of projects. Identifies and monitors the resources necessary to implement and "
     "maintain HR projects. Identifies when resource allocation is inconsistent with project needs "
     "and makes adjustments as necessary. Demonstrates agility and adaptability when project "
     "requirements, goals or constraints change. "
     "Advanced HR Professionals: Translates HR's vision, strategic direction and long-term goals "
     "into specific projects and initiatives with clear timelines and goals. Monitors the progress "
     "of HR initiatives toward achievement of HR's vision, strategic direction and long-term goals. "
     "Collaborates with leadership to remove obstacles to the successful implementation of HR "
     "initiatives. Obtains and deploys organizational resources and monitors their effectiveness. "
     "Ensures accountability for the implementation of project plans and initiatives."),

    ("SHRM-1", "HRM-1.01.04", "Influence",
     "All HR Professionals: Builds credibility as an HR expert within and outside of the "
     "organization. Promotes buy-in among organizational stakeholders for HR initiatives. "
     "Motivates HR staff and other stakeholders to support HR's vision and goals. Serves as an "
     "advocate for the organization or employees to advance the organization's strategic direction "
     "and goals. Shares opinions about important issues, regardless of risk or discouragement from "
     "others. "
     "Advanced HR Professionals: Promotes the role of the HR function in achieving the "
     "organization's mission, vision and goals. Builds credibility for the organization regionally, "
     "nationally or internationally as an HR expert. Serves as an influential voice for HR "
     "strategies, philosophies and initiatives within the organization. Advocates for the "
     "implementation of evidence-based HR solutions. Inspires HR staff, non-HR customers and "
     "executive-level organizational stakeholders to support and pursue the organization's "
     "strategic direction, vision and long-term goals. Builds consensus among leaders about the "
     "organization's strategic direction and long-term goals. Uses HR knowledge and skills to "
     "influence business strategy. Empowers leaders to create an environment where there is "
     "tolerance for risk taking and workers feel comfortable sharing ideas."),

    ("SHRM-1", "HRM-1.02.01", "Personal Integrity",
     "All HR Professionals: Shows consistency between stated and enacted values. Acknowledges "
     "mistakes and demonstrates accountability for actions. Recognizes explicit and unconscious "
     "biases in oneself and others, and takes steps to increase self-awareness. Serves as a role "
     "model of personal integrity and high ethical standards. "
     "Advanced HR Professionals: Brings potential conflicts of interest or unethical behaviors to "
     "the attention of leaders and executives. Helps others to identify, understand and address "
     "their biases. Holds others accountable to their commitments."),

    ("SHRM-1", "HRM-1.02.02", "Professional Integrity",
     "All HR Professionals: Maintains privacy as appropriate and complies with laws and regulations "
     "mandating a duty to report unethical behavior. Uses discretion appropriately when "
     "communicating sensitive information, and informs stakeholders of the limits of "
     "confidentiality and privacy. Maintains current knowledge of ethics laws, standards, "
     "legislation and emerging trends that may affect organizational HR practice. Leads HR "
     "investigations in a thorough, timely and impartial manner. Establishes oneself as credible "
     "and trustworthy. Does not take actions based on personal biases. Applies, and challenges "
     "when necessary, the organization's ethics and integrity policies. Manages political and "
     "social pressures when making decisions and when implementing and enforcing HR programs, "
     "practices and policies. Provides open, honest and constructive feedback to colleagues when "
     "situations involving questions of ethics arise. Balances ethics, integrity, organizational "
     "success, employee advocacy, organizational mission and values, laws and regulations, and "
     "organizational policies and procedures. Seeks opportunities to learn new skills and improve "
     "existing skills to become a stronger HR professional. "
     "Advanced HR Professionals: Withstands politically motivated pressure when developing or "
     "implementing strategy, initiatives or long-term goals. Balances ethics, integrity, "
     "organizational success, employee advocacy, and organizational mission and values when "
     "creating strategy, initiatives or long-term goals. Establishes the HR team as a credible "
     "and trustworthy resource. Promotes the alignment of HR and business practices with ethics "
     "laws and standards. Makes difficult decisions that align with organizational values and "
     "ethics. Applies power or authority appropriately without seeking personal gain or benefit. "
     "Demonstrates agility and courage when making difficult decisions or handling challenging "
     "situations."),

    ("SHRM-1", "HRM-1.02.03", "Ethical Agent",
     "All HR Professionals: Empowers all employees to report unethical behaviors and conflicts of "
     "interest without fear of reprisal. Takes steps to mitigate the influence of bias in HR and "
     "business decisions. Maintains appropriate levels of transparency for HR programs, practices "
     "and policies. Identifies, evaluates and communicates to leadership potential ethical risks "
     "and conflicts of interest. Ensures staff members have access to and understand the "
     "organization's ethical standards and policies. "
     "Advanced HR Professionals: Advises senior management of organizational risks and conflicts "
     "of interest. Collaborates with leaders to support internal ethics controls. Develops and "
     "provides expertise for HR policies, standards and other internal ethics controls to minimize "
     "organizational risks from unethical practices. Creates and oversees HR programs, practices "
     "and policies that drive an ethical culture, encourage employees to report unethical behaviors, "
     "and protect the confidentiality of employees and data. Communicates a vision for an "
     "organizational culture in which there is consistency between the organization's stated and "
     "enacted values. Develops HR programs, practices and policies that meet high standards of "
     "ethics and integrity. Designs and oversees systems to ensure that all investigations are "
     "conducted in a thorough, timely and impartial manner. Audits and monitors adherence to HR "
     "programs, practices and policies pertaining to ethics. Designs and oversees learning and "
     "development programs covering ethics. Implements and maintains a culture and system that "
     "encourages all employees to report unethical practices and behaviors."),

    ("SHRM-1", "HRM-1.03.01", "Connecting I&D to Organizational Performance",
     "All HR Professionals: Reviews HR programs, practices and policies to ensure parity for all. "
     "Designs and executes I&D initiatives and programs to achieve business goals. Collects, "
     "reviews, analyzes and communicates I&D metric results to show measurable impacts on "
     "organizational objectives. Demonstrates an understanding of and advocates for the strategic "
     "connection between inclusion and diversity practices and organizational success. Designs, "
     "recommends, implements and audits HR programs, practices and policies intended to promote "
     "inclusion and diversity. "
     "Advanced HR Professionals: Partners with business leaders and HR professionals to develop, "
     "implement and manage enterprisewide programs, practices and policies that lead to an "
     "inclusive and diverse workforce. Assesses an organization's talent lifecycle for inclusiveness "
     "and diversity using I&D metrics. Incorporates the results of equity audits into HR strategy "
     "and programs. Develops and advocates for the organizational business case for I&D. Partners "
     "with leaders to incorporate I&D goals into the organization's strategic plan. Sets and tracks "
     "I&D goals and metrics to measure the impact on organizational objectives. Identifies and "
     "applies changes in the workforce and workplace related to I&D that are necessary to help an "
     "organization meet key business objectives. Drives an HR strategy that embraces and leverages "
     "inclusion, diversity and cultural differences for organizational success. Evaluates the "
     "organization's current cultural climate and identifies areas for improvement."),

    ("SHRM-1", "HRM-1.03.02", "Building the Infrastructure for an Inclusive and Diverse Culture",
     "All HR Professionals: Recognizes, supports and advocates on behalf of an inclusive workforce "
     "across race, gender, sexual orientation, ethnicity, religious beliefs, country of origin, "
     "education, abilities (including invisible abilities and digital accessibility), neurodiversity, "
     "and the intersectionality of the elements of diversity. Communicates the benefits of I&D to "
     "employees and leaders. Identifies opportunities to enhance the equity of organizational "
     "policies and procedures to all employees. Implements and manages benefits and HR programs "
     "that support the needs of a diverse workforce. Partners with internal and external "
     "stakeholders to hire and promote employees from diverse groups across a variety of dimensions. "
     "Promotes the benefits of an inclusive, diverse workforce. Fosters an organizational culture "
     "that values equal opportunities for all and promotes inclusion and diversity. "
     "Advanced HR Professionals: Advocates to leadership to eliminate barriers and obstacles that "
     "hinder workforce inclusion. Drives a culture that encourages authenticity and courageous, "
     "honest I&D-related conversations among employees. Identifies, advocates for and manages "
     "benefits and programs that support an inclusive, diverse, and unbiased workforce. Drives HR "
     "initiatives, programs and policies that support the organization's efforts to be more "
     "inclusive of all employees. Ensures that learning and development programs about inclusion, "
     "diversity and cultural sensitivity are provided to employees at all levels of the "
     "organization."),

    ("SHRM-1", "HRM-1.03.03", "Ensuring Impartiality & Fairness",
     "All HR Professionals: Develops and maintains knowledge of all applicable laws, current "
     "trends and HR management best practices relating to I&D. Contributes to the development and "
     "reinforcement of an organizational culture that provides access, equal opportunity and equity "
     "for all. Demonstrates a general awareness and understanding of and respect for cultural "
     "differences. Promotes inclusion and acceptance of colleagues from different cultures in daily "
     "interactions. Uses the organization's I&D policies and philosophy to inform business "
     "decisions and the implementation of HR programs, practices and policies. Ensures that HR "
     "programs, practices and policies are applied consistently and respectfully for all. "
     "Advanced HR Professionals: Ensures HR staff members have up-to-date knowledge of trends and "
     "HR management best practices relating to I&D that also align with all applicable laws. "
     "Designs and manages HR programs, practices and policies that promote an organizational "
     "culture that provides access, equal opportunity and equity for all. Plans interventions to "
     "resolve identified inequities. Seeks out and hires a team of HR professionals that is diverse "
     "across a variety of dimensions. Drives and develops HR initiatives that will be applied "
     "equally, consistently and fairly to all staff."),

    ("SHRM-1", "HRM-1.03.04", "Cultivating an Inclusive and Diverse Culture",
     "All HR Professionals: Identifies and implements employee accommodation solutions that align "
     "with all applicable laws. Identifies and addresses evidence of bias, stereotyping, "
     "microaggressions and exclusionary behaviors in the workplace. Provides professional "
     "development, mentoring, coaching and guidance on cultural and diversity differences and "
     "practices to employees at all levels of the organization. Facilitates opportunities that "
     "encourage employees to work with those who possess diverse experiences and backgrounds. "
     "Supports workplace culture and practices that ensure mutual respect, trust and zero-tolerance "
     "of retaliation. Guides managers to recognize behavioral distinctions between performance "
     "issues and I&D differences. Enables others to adapt behavior to navigate different cultural "
     "conditions, situations and people. Identifies and reconciles organizational practices and "
     "policies that are in conflict with cultural norms. "
     "Advanced HR Professionals: Creates and manages opportunities that encourage employees to "
     "work with those who possess diverse experiences and backgrounds. Develops policies and "
     "programs to create a workplace culture and team that support and reinforce the principles of "
     "psychological safety. Advises business leaders on how to develop more empathetic and "
     "inclusive behaviors."),

    ("SHRM-1", "HRM-1.03.05", "Operating in a Global Environment",
     "All HR Professionals: Conducts business with an understanding of and respect for "
     "cross-cultural differences in customs and acceptable behaviors. Demonstrates an understanding, "
     "from a global perspective, of the organization's line of business. Customizes HR initiatives "
     "to local needs by applying an understanding of cultural differences. Conducts business with "
     "an understanding of and respect for differences in rules, laws, regulations, and accepted "
     "business operations and practices. Applies knowledge of global trends when implementing or "
     "maintaining HR programs, practices and policies. Operates with a global mindset while "
     "remaining sensitive to local issues and needs. "
     "Advanced HR Professionals: Creates an HR strategy that incorporates the organization's "
     "global competencies and perspectives on organizational success. Analyzes global HR trends, "
     "economic conditions, labor markets and legal environments to set HR's strategic direction "
     "and to inform development and implementation of HR initiatives. Analyzes global HR trends, "
     "economic conditions, labor markets and legal environments to evaluate the impact of "
     "inclusion and diversity on the organization's HR strategy."),

    # =========================================================
    # INTERPERSONAL CLUSTER
    # =========================================================

    ("SHRM-2", "HRM-2.01.01", "Networking",
     "All HR Professionals: Develops, maintains and leverages a network of professional contacts "
     "within the organization, including peers in both HR and non-HR roles, HR customers, and "
     "stakeholders. Develops and maintains a network of external partners (such as vendors). "
     "Develops and maintains a network of professional colleagues in the HR community at large for "
     "professional development and to fill business needs. "
     "Advanced HR Professionals: Creates opportunities for HR employees to network and build "
     "relationships with higher-level leaders in the organization and in the HR community at large. "
     "Develops, maintains and leverages a network of contacts within the organization (such as "
     "leaders from other business units) and outside of the organization (examples include members "
     "of legislative bodies, community leaders, union heads, external HR leaders)."),

    ("SHRM-2", "HRM-2.01.02", "Relationship Building",
     "All HR Professionals: Develops and maintains mutual trust and respect with colleagues. "
     "Develops and maintains a pattern of reciprocal exchanges of support, information and other "
     "valued resources with colleagues. Demonstrates concern for the well-being of colleagues. "
     "Establishes a strong and positive reputation, within and outside the organization, as an "
     "open and approachable HR professional. Ensures all HR team member and stakeholder voices are "
     "heard and acknowledged. Identifies and leverages areas of common interest among stakeholders "
     "to foster the success of HR initiatives. Develops working relationships with supervisors and "
     "HR leaders by promptly and effectively responding to work assignments, communicating goal "
     "progress and project needs, and managing work activities. Understands the interests of "
     "executives and leaders within the organization. Uses technology to build and maintain strong "
     "relationships with individuals who work at other work locations. "
     "Advanced HR Professionals: Develops HR's objectives and goals for relationship management. "
     "Develops and maintains relationships in the HR community at large through leadership "
     "positions in other organizations. Leverages relationships to learn about best practices for "
     "and new approaches to building competitive advantage."),

    ("SHRM-2", "HRM-2.01.03", "Teamwork",
     "All HR Professionals: Builds engaged relationships with team members through trust, "
     "task-related support, decision-making and direct communication. Fosters collaboration and "
     "open communication among stakeholders and team members, regardless of location or employment "
     "type. Supports a team-oriented organizational culture. Creates and/or participates in "
     "project teams made up of HR and non-HR employees. Embraces opportunities to lead a team. "
     "Identifies and fills missing or unfulfilled team roles. "
     "Advanced HR Professionals: Fosters an organizational culture that supports "
     "intraorganizational teamwork and collaboration. Creates and leads teams with senior leaders "
     "from across the organization. Designs and oversees HR initiatives that promote effective "
     "team processes and environments."),

    ("SHRM-2", "HRM-2.01.04", "Negotiation",
     "All HR Professionals: Maintains a professional demeanor during negotiation discussions. "
     "Applies an understanding of the needs, interests, issues and bargaining position of all "
     "parties to negotiation discussions. Offers appropriate concessions to promote progress toward "
     "an agreement. Adheres to applicable negotiation- and bargaining-related laws and regulations. "
     "Evaluates progress toward an agreement. Identifies an ideal solution or end state for "
     "negotiations, monitors progress toward that end state and ends negotiations when appropriate. "
     "Advanced HR Professionals: Negotiates with stakeholders within and outside of the "
     "organization in complex and high-stakes negotiations. Defines the parameters of negotiating "
     "boundaries on behalf of the HR unit. Achieves a mutually acceptable agreement in difficult "
     "and complex negotiations."),

    ("SHRM-2", "HRM-2.01.05", "Conflict Management",
     "All HR Professionals: Resolves and/or mediates conflicts in a respectful, appropriate and "
     "impartial manner, and refers them to a higher level when warranted. Identifies and addresses "
     "the underlying causes of conflict. Facilitates difficult interactions among employees to "
     "achieve optimal outcomes. Encourages productive and respectful task-related conflict and "
     "uses it to facilitate change. Serves as a positive role model for productive conflict. "
     "Identifies and resolves conflict that is counterproductive or harmful. "
     "Advanced HR Professionals: Designs and oversees conflict resolution strategies and processes "
     "throughout the organization. Facilitates difficult interactions among senior leaders to "
     "achieve optimal outcomes. Identifies and reduces potential sources of conflict when proposing "
     "new HR strategies or initiatives. Mediates or resolves escalated conflicts."),

    ("SHRM-2", "HRM-2.02.01", "Delivering Messages",
     "All HR Professionals: Presents needed information to stakeholders on a regular basis and "
     "refrains from presenting unneeded information. Uses an understanding of the audience to "
     "craft the content of communications and choose the best formal or informal medium. Uses "
     "appropriate business terms and vocabulary. Ensures the delivered message is clear and "
     "understood by the listener. Crafts clear, organized, effective and error-free messages that "
     "are consistent with the organization's brand. Creates persuasive and compelling arguments. "
     "Advanced HR Professionals: Demonstrates fluency in the business language of senior leaders. "
     "Communicates difficult or negative messages in an honest, accurate and respectful manner. "
     "Comfortably presents to audiences of all sizes and backgrounds."),

    ("SHRM-2", "HRM-2.02.02", "Exchanging Organizational Information",
     "All HR Professionals: Effectively communicates HR programs, practices and policies to both "
     "HR and non-HR employees. Helps non-HR managers communicate HR issues. Voices support for HR "
     "and organizational initiatives in communications with stakeholders. Effectively communicates "
     "with HR leaders. "
     "Advanced HR Professionals: Communicates HR's vision, strategy, goals and culture to senior "
     "leaders and HR staff. Articulates to senior leaders the alignment of HR's strategies and "
     "goals with the organization's. Implements policies and initiatives that create channels for "
     "open communication throughout the organization, across and within levels of responsibility. "
     "Prepares and delivers messages on important, high-visibility HR and organizational issues to "
     "senior- and board-level audiences."),

    ("SHRM-2", "HRM-2.02.03", "Listening",
     "All HR Professionals: Listens actively and empathetically to others' views and concerns. "
     "Welcomes the opportunity to hear competing points of view and does not take criticism "
     "personally. Seeks further information to clarify ambiguity. Promptly responds to and "
     "addresses stakeholder communications. Interprets and understands the context of, motives "
     "for and reasoning in received communications. Solicits regular feedback from employees and "
     "leaders, and adjusts as necessary. "
     "Advanced HR Professionals: Develops an organizational culture in which upward communication "
     "is encouraged and leaders are receptive to staff views and opinions. Establishes processes "
     "to gather feedback from the entire organization about the HR function."),

    # =========================================================
    # BUSINESS CLUSTER
    # =========================================================

    ("SHRM-3", "HRM-3.01.01", "Business and Competitive Awareness",
     "All HR Professionals: Uses organizational and external resources to learn about the "
     "organization's business operations, functions, products and services. Uses organizational "
     "and external resources to learn about the political, economic, social, technological, legal "
     "and environmental (PESTLE) trends that influence the organization. Applies knowledge of the "
     "organization's business operations, functions, products and services to implement HR "
     "solutions and inform business decisions. Applies knowledge of the organization's industry "
     "and PESTLE trends to implement HR solutions and inform HR decisions. "
     "Advanced HR Professionals: Gathers and applies business intelligence about PESTLE trends to "
     "define HR's strategic direction and long-term goals. Applies expert knowledge of the "
     "organization's business operations, functions, products and services when setting HR's "
     "strategic direction and long-term goals. Applies an understanding of the labor market when "
     "developing a strategy to manage and compete for talent. Participates in advocacy activities "
     "involving government policy and proposed regulations related to the organization's HR "
     "strategies and long-term goals."),

    ("SHRM-3", "HRM-3.01.02", "Business Analysis",
     "All HR Professionals: Uses cost-benefit analysis, organizational metrics, key performance "
     "indicators (KPIs) and critical data insights to inform business decisions. Applies principles "
     "of finance, marketing, economics, sales, technology, law and business systems to internal HR "
     "programs, practices and policies. Uses HR information systems (HRIS) and business technology "
     "to solve problems and address needs. "
     "Advanced HR Professionals: Designs, implements and evaluates HR initiatives with "
     "consideration of value added, ROI, utility, revenue, profit and loss statements and other "
     "business indicators. Uses risk assessment to inform HR's and the organization's strategic "
     "direction and long-term goals. Determines the budget and resource requirements of HR "
     "initiatives. Examines organizational problems and opportunities in terms of integrating HR "
     "solutions that maximize ROI and strategic effectiveness."),

    ("SHRM-3", "HRM-3.01.03", "Strategic Alignment",
     "All HR Professionals: Demonstrates an understanding of the relationship between effective "
     "HR and effective core business functions. Aligns decisions with HR's and the organization's "
     "strategic direction and goals. Creates and communicates the business case, or provides the "
     "data to build the case, for HR initiatives and their influence on efficient and effective "
     "organizational functioning. "
     "Advanced HR Professionals: Defines and communicates HR's and the organization's strategy, "
     "goals and challenges in terms of business results. Aligns HR's strategic direction and "
     "long-term goals with the organization's overall business strategy and objectives. Applies "
     "the perspective of systems thinking to make HR and business decisions. Drives key business "
     "results by developing strategies and long-term goals that account for senior leaders' input. "
     "Serves as a strategic contributor to organizational decision-making on fiscal issues, "
     "product/service lines, operations, human capital and technology. Evaluates all proposed "
     "business cases for HR initiatives."),

    ("SHRM-3", "HRM-3.02.01", "Evaluating Business Challenges",
     "All HR Professionals: Partners with stakeholders to understand the organization's current "
     "and future HR challenges, and identify HR needs and opportunities for improvement. Informs "
     "stakeholders about current and future HR-related threats and liabilities. Advises "
     "stakeholders on existing HR programs, practices and policies that impede or support business "
     "success. "
     "Advanced HR Professionals: Works with leadership to identify how HR can improve business "
     "outcomes and support the organization's strategic direction and long-term goals."),

    ("SHRM-3", "HRM-3.02.02", "Designing HR Solutions",
     "All HR Professionals: Partners with stakeholders to suggest HR solutions that are creative, "
     "innovative, effective and based on best practices and/or research. Provides guidance to "
     "non-HR managers regarding HR practices, compliance, laws, regulations and ethics. Defines "
     "clear goals and outcomes for HR solutions, and uses them to drive solution design. "
     "Advanced HR Professionals: Works with key internal stakeholders to identify initiatives that "
     "minimize threats and liabilities. Determines the strategic approach to remediation of "
     "HR-related threats and liabilities. Works with business leaders to create innovative, "
     "evidence-based talent management strategies that align with and drive the organization's "
     "strategy. Designs and oversees evidence-based long-term strategic HR and business solutions."),

    ("SHRM-3", "HRM-3.02.03", "Advising on HR Solutions",
     "All HR Professionals: Provides guidance to other HR professionals, non-HR managers and "
     "business unit teams on implementation of HR-related solutions. Works with business partners "
     "to overcome obstacles to implementation of HR solutions. Provides follow-up to and ongoing "
     "support for implementation of HR solutions to ensure their continued effectiveness. Ensures "
     "that the implementation of HR solutions adheres to defined goals and outcomes. "
     "Advanced HR Professionals: Provides ongoing support and HR solutions to business unit "
     "leaders on the organization's strategic direction. Encourages staff and leaders to provide "
     "input on strategic HR and business decisions. Works with leaders to overcome obstacles to "
     "implementation of HR initiatives. Integrates HR solutions with related organizational "
     "processes, systems, and other business or management initiatives."),

    ("SHRM-3", "HRM-3.02.04", "Change Management",
     "All HR Professionals: Recommends ways to improve HR programs, practices and policies. "
     "Promotes buy-in among organizational stakeholders when implementing change initiatives. "
     "Builds buy-in among staff for organizational change. Aligns and deploys HR programs to "
     "support change initiatives. "
     "Advanced HR Professionals: Works with executives to identify when and where change is or is "
     "not needed. Builds buy-in among leadership and staff at all levels for organizational change. "
     "Defines change objectives and goals. Oversees implementation of change initiatives across "
     "business units and throughout the organization. Partners with business leaders to achieve "
     "change objectives and goals. Provides support to HR staff at all levels during change "
     "initiatives."),

    ("SHRM-3", "HRM-3.02.05", "Service Excellence",
     "All HR Professionals: Identifies, defines and clarifies needs and requirements of "
     "stakeholders, and reports on the status of HR services provided and results achieved. "
     "Responds promptly, courteously and openly to stakeholder requests, and takes ownership of "
     "stakeholder needs. Identifies and resolves risks and early-stage problems in meeting "
     "stakeholder needs. Manages interactions with vendors and suppliers to maintain service "
     "quality. "
     "Advanced HR Professionals: Designs and oversees HR programs, practices and policies that "
     "ensure a strong, high-quality stakeholder service culture in the HR function. Oversees HR's "
     "stakeholder service objectives and outcomes. Identifies larger system needs and issues "
     "influencing market requirements, and engages outside stakeholders to help meet requirements "
     "that go beyond HR's functional assignment. Develops and promotes an organizational culture "
     "that excels at meeting stakeholder needs."),

    ("SHRM-3", "HRM-3.03.01", "Data Advocate",
     "All HR Professionals: Demonstrates an understanding of the importance of using data to "
     "inform business decisions and recommendations. Promotes the importance of evidence-based "
     "decision-making. Promotes the importance of validating HR programs, practices and policies "
     "to ensure that they achieve desired outcomes. Identifies decision points that can be informed "
     "by data and evidence. "
     "Advanced HR Professionals: Promotes the role of evidence in setting and validating HR's "
     "strategic direction and long-term goals. Supports an organizational culture that promotes "
     "the collection and incorporation of data into decision-making. Promotes the use of HR "
     "metrics for understanding organizational performance. Ensures that the HR function uses "
     "data to inform decision-making and the development and evaluation of HR initiatives."),

    ("SHRM-3", "HRM-3.03.02", "Data Gathering",
     "All HR Professionals: Maintains working knowledge of data collection, research methods, "
     "benchmarks and HR metrics. Identifies sources of the most relevant data for solving "
     "organizational problems and answering questions. Gathers data using appropriate methods to "
     "inform and monitor organizational solutions. Scans external sources for data relevant to the "
     "organization. Benchmarks HR initiatives and outcomes against the organization's competition "
     "and other relevant comparison groups. "
     "Advanced HR Professionals: Ensures that resources and processes are in place to facilitate "
     "systematic collection of data and to inform HR's strategic direction and long-term goals. "
     "Identifies new sources of data or new methods of data collection to inform and evaluate HR "
     "initiatives. Interacts with leaders outside the organization to collect data relevant to HR."),

    ("SHRM-3", "HRM-3.03.03", "Data Analysis",
     "All HR Professionals: Maintains working knowledge of statistics and measurement concepts. "
     "Identifies potentially misleading or flawed data, results, tools or systems. Conducts "
     "analyses to identify evidence-based best practices, evaluate HR initiatives and determine "
     "critical findings. Maintains objectivity when interpreting data. Identifies gaps in data "
     "based on analysis and seeks missing data. "
     "Advanced HR Professionals: Maintains advanced knowledge of statistics and measurement "
     "concepts and tools. Oversees comprehensive and systematic evaluations of the organization's "
     "HR programs, practices and policies and their interconnections. Critically reviews and "
     "interprets the results of analyses to identify evidence-based best practices, evaluate HR "
     "initiatives and determine critical findings."),

    ("SHRM-3", "HRM-3.03.04", "Evidence-Based Decision-Making",
     "All HR Professionals: Reports key findings to business and HR leaders. Uses research "
     "findings to evaluate different courses of action and their impacts on the organization. "
     "Applies data-driven knowledge and best practices from one situation to the next. Ensures HR "
     "programs, practices and policies reflect research findings and best practices. Objectively "
     "examines HR programs, practices and policies in light of data and/or source of the data. "
     "Uses data to explain and support business decisions to employees and leaders. "
     "Advanced HR Professionals: Communicates critical data analysis findings and their "
     "implications for HR's strategic direction and goals to senior leaders. Uses research "
     "findings to inform HR's strategic direction and long-term goals. Develops best practices "
     "based on evidence from industry literature, peer-reviewed research, experience and other "
     "sources. Sponsors evidence-based initiatives for process improvement. Uses data to support "
     "business cases."),

    # =========================================================
    # PEOPLE KNOWLEDGE DOMAIN
    # =========================================================

    ("SHRM-4", "HRM-4.01.01", "HR Strategy",
     "All HR Professionals: Uses the perspective of systems thinking to understand how the "
     "organization operates. Informs business decisions with knowledge of the strategy and goals "
     "of HR and the organization. Develops and implements an individual action plan for executing "
     "HR's strategy and goals. Uses benchmarks, industry metrics and workforce trends to understand "
     "the organization's market position and competitive advantage. Informs HR leadership of new "
     "or overlooked opportunities to align HR's strategy with the organization's. Provides HR "
     "leadership with timely and accurate information required for strategic decision-making. "
     "Advanced HR Professionals: Identifies the ways in which the HR function can support the "
     "organization's strategy and goals. Aligns strategic management and planning activities with "
     "organizational mission, vision and values. Engages business leaders in strategic analysis "
     "and planning. Evaluates HR's critical activities in terms of value added, impact and utility, "
     "using cost-benefit analysis, revenue, profit-and-loss estimates, and other leading or lagging "
     "indicators. Provides HR-focused expertise to business leaders when formulating the "
     "organization's strategy and goals. Develops and implements HR strategy, vision and goals "
     "that align with and support the organization's strategy and goals. Ensures that HR strategy "
     "creates and sustains the organization's competitive advantage."),

    ("SHRM-4", "HRM-4.02.01", "Talent Acquisition",
     "All HR Professionals: Understands the talent needs of the organization or business unit. "
     "Uses a wide variety of talent sources and recruiting methods to attract a qualified and "
     "diverse pool of applicants. Uses technology to support effective and efficient approaches "
     "to sourcing, recruiting and onboarding employees. Promotes and uses the EVP and employment "
     "brand for sourcing and recruiting applicants. Uses the most appropriate hiring methods, "
     "assessments and scoring to evaluate a candidate's technical skills, positional fit and "
     "alignment with the organization's competency needs based on job requirements. Conducts "
     "appropriate pre-employment screening. Implements effective and personalized onboarding and "
     "orientation programs for new employees. Designs job descriptions to meet the organization's "
     "resource needs. Complies with local and country-specific laws and regulations governing "
     "talent acquisition. Advises and coaches hiring managers on best practices related to job "
     "descriptions, interviews, onboarding and candidate experience. "
     "Advanced HR Professionals: Analyzes staffing levels and projections to forecast workforce "
     "needs. Develops strategies for sourcing and acquiring a workforce that meets the "
     "organization's needs. Establishes an EVP and employment branding strategy that supports "
     "recruitment of high-quality job applicants. Designs and oversees effective strategies and "
     "systems for sourcing, recruiting and evaluating qualified job candidates. Designs and "
     "oversees employee onboarding processes. Designs and oversees valid and systematic programs "
     "for assessing the effectiveness of talent acquisition activities."),

    ("SHRM-4", "HRM-4.03.01", "Employee Engagement & Retention",
     "All HR Professionals: Designs, administers, analyzes and interprets surveys on employee "
     "engagement, job satisfaction and culture using best practices. Administers and supports HR "
     "and organizational programs designed to improve the employee experience, including engagement "
     "and culture. Identifies program opportunities to create more engaging or motivating jobs. "
     "Monitors changes in turnover and retention metrics, and ensures that leadership is aware of "
     "such changes. Coaches supervisors on creating positive working relationships with their "
     "employees. Trains stakeholders to use the organization's performance management systems. "
     "Helps stakeholders understand the elements of satisfactory employee performance and "
     "performance management. Implements and monitors processes that measure the effectiveness "
     "of performance management systems. "
     "Advanced HR Professionals: Collaborates with business leaders to define an organizational "
     "strategy to create a positive employee experience and an engaged workforce. Implements best "
     "practices for employee retention in HR programs, practices and policies. Designs, oversees "
     "and communicates an action plan to address the findings of surveys on employee engagement, "
     "job satisfaction and culture. Communicates the results of surveys of employee attitudes and "
     "culture. Designs and oversees HR and organizational programs designed to improve employee "
     "engagement and satisfaction. Holistically monitors the organization's metrics on employee "
     "attitudes, turnover and retention. Designs and oversees best-practices-based employee "
     "performance management systems that meet the organization's talent management needs. "
     "Designs and oversees processes to measure the effectiveness of performance management "
     "systems."),

    ("SHRM-4", "HRM-4.04.01", "Learning & Development",
     "All HR Professionals: Uses best practices to evaluate data on gaps in employees' "
     "competencies and skills. Uses best practices to develop and deliver learning and development "
     "activities that close gaps in employees' competencies and skills. Uses all available "
     "resources (such as vendors) to develop, deliver and evaluate effective learning and "
     "development programs. Creates internal social networks to facilitate knowledge-sharing among "
     "employees. Creates IDPs in collaboration with supervisors and employees. Administers and "
     "supports programs to promote knowledge transfer. "
     "Advanced HR Professionals: Designs and oversees efforts to collect data on critical gaps in "
     "employees' competencies and skills. Provides guidance to identify and develop critical "
     "competencies that meet the organization's talent needs. Monitors the effectiveness of "
     "programs for emerging leaders and leadership development. Creates long-term organizational "
     "strategies to develop talent. Creates strategies to ensure the retention of organizational "
     "knowledge."),

    ("SHRM-4", "HRM-4.05.01", "Total Rewards",
     "All HR Professionals: Collects, compiles and interprets compensation and benefits data from "
     "various sources. Implements appropriate pay, benefits, incentive, separation and severance "
     "systems and programs. Complies with best practices for and laws and regulations governing "
     "compensation and benefits. Differentiates among government-mandated, government-provided "
     "and voluntary benefits approaches. Performs accurate job evaluations to determine "
     "appropriate compensation and benefits. "
     "Advanced HR Professionals: Designs and oversees organizational compensation and benefits "
     "philosophies, strategies and plans that align with the organization's strategic direction "
     "and talent needs. Designs and oversees executive compensation approaches that directly "
     "connect individual performance and desired behaviors to organizational success. Ensures the "
     "internal equity of compensation systems. Re-evaluates the organization's total rewards "
     "package regularly, and adjusts as needed."),

    # =========================================================
    # ORGANIZATION KNOWLEDGE DOMAIN
    # =========================================================

    ("SHRM-5", "HRM-5.01.01", "Structure of the HR Function",
     "All HR Professionals: Adapts work style to fit the organization's HR service model to ensure "
     "timely and consistent delivery of services to stakeholders. Seeks feedback from stakeholders "
     "to identify opportunities to improve HR function. Acts as HR point-of-service contact for "
     "key stakeholders within a division or group. Consults with all levels of leadership and "
     "management on HR issues. Coordinates with other HR functions to ensure timely and consistent "
     "delivery of services to stakeholders. Ensures that outsourced and/or automated HR functions "
     "are integrated with other HR activities. Analyzes and interprets key performance indicators "
     "(KPIs) to understand the effectiveness of the HR function. Works collaboratively with "
     "departments outside of HR to deliver and support HR-related functions. "
     "Advanced HR Professionals: Designs, implements and adjusts the HR service model for the "
     "organization to ensure efficient and effective delivery of services to stakeholders. Creates "
     "long-term goals and implements changes that address feedback from stakeholders identifying "
     "opportunities for HR function improvements. Ensures that all elements of the HR function "
     "are aligned and integrated, and that they provide timely and consistent delivery of services "
     "to stakeholders. Identifies opportunities to improve HR operations by outsourcing work or "
     "implementing technologies that automate HR functions. Designs and oversees programs to "
     "collect, analyze and interpret HR-function metrics to evaluate the effectiveness of HR "
     "activities in supporting organizational success."),

    ("SHRM-5", "HRM-5.02.01", "Organizational Effectiveness & Development",
     "All HR Professionals: Ensures that key documents and systems accurately reflect workforce "
     "activities. Supports change initiatives to increase the effectiveness of HR systems and "
     "processes. Identifies areas in the organization's structures, processes and procedures that "
     "need change. Recommends methods to eliminate barriers to organizational effectiveness and "
     "development. Collects and analyzes data on organizational performance and the value of HR "
     "initiatives to the organization. "
     "Advanced HR Professionals: Aligns HR's strategy and activities with the organization's "
     "mission, vision, values and strategy. Regularly monitors results against performance "
     "standards and goals in support of the organization's strategy. Establishes measurable goals "
     "and objectives to create a culture of accountability, continuous experimentation and "
     "improvement. Consults on, plans and designs organizational structures that align with the "
     "effective delivery of activities in support of the organization's strategy. Assesses "
     "organizational needs to identify critical competencies for operational effectiveness. "
     "Designs and oversees change initiatives to increase the effectiveness of HR systems and "
     "processes. Ensures that HR initiatives demonstrate measurable value to the organization."),

    ("SHRM-5", "HRM-5.03.01", "Workforce Management",
     "All HR Professionals: Assesses the competencies needed to support and grow the organization, "
     "and identifies gaps and misalignment of staffing levels. Implements approaches to ensure "
     "that appropriate workforce staffing levels and competencies exist to meet the organization's "
     "goals and objectives. Forecasts future workforce needs, and plans strategies to develop "
     "workforce competencies that support the organization's goals and objectives. Administers and "
     "supports approaches to ensure the organization's long-term leadership needs are met. "
     "Supports strategies for restructuring the organization's workforce. Provides employees with "
     "continuous learning opportunities, including opportunities for upskilling and reskilling. "
     "Advanced HR Professionals: Evaluates how the organization's strategy and goals align with "
     "future and current staffing levels and workforce competencies. Develops strategies to "
     "maintain a robust workforce that has the talent to carry out the organization's current and "
     "future strategy and goals. Coordinates with business leaders to create strategies that "
     "address the organization's long-term leadership needs. Develops strategies for restructuring "
     "the organization's workforce."),

    ("SHRM-5", "HRM-5.04.01", "Employee & Labor Relations",
     "All HR Professionals: Develops and implements workplace policies, handbooks and codes of "
     "conduct. Provides guidance to employees on the terms and implications of their employment "
     "agreement and the organization's policies and procedures. Advises managers on how to "
     "supervise difficult employees, handle disruptive behaviors and respond with the appropriate "
     "level of corrective action. Conducts investigations into employee misconduct and suggests "
     "disciplinary action when necessary. Manages employee grievance and discipline processes. "
     "Resolves workplace labor disputes internally. Supports interactions and negotiations with "
     "employee representatives. "
     "Advanced HR Professionals: Consults on and develops an effective organized labor strategy "
     "to achieve the organization's desired impact on itself and its workforce. Educates employees, "
     "managers and leaders at all levels about the organization's labor strategy and its impact on "
     "the achievement of goals and objectives. Educates employees at all levels about changes in "
     "the organization's policies. Coaches and counsels managers on how to operate within the "
     "parameters of organizational policy, labor agreements and employment agreements. Oversees "
     "employee investigations and progressive disciplinary actions. Manages interactions and "
     "negotiations with employee representatives. Serves as the primary representative of the "
     "organization's interests in activities related to organized labor management."),

    ("SHRM-5", "HRM-5.05.01", "Technology Management",
     "All HR Professionals: Implements and uses technology solutions that support or facilitate "
     "delivery of effective HR services and storage of critical candidate and employee data. "
     "Implements technology that integrates with and complements other enterprise information "
     "systems, software and technology. Strategically integrates technology-driven self-service "
     "approaches that enable managers and employees to perform self-service and people management "
     "functions. Uses technologies in a manner that protects workforce data. Provides guidance to "
     "stakeholders on effective standards and policies for use of technologies in the workplace. "
     "Coordinates and manages vendors implementing HR technology solutions. Uses technologies to "
     "collect, access and analyze data and information to understand business challenges and "
     "recommend evidence-based solutions. Develops, implements and monitors technology-driven "
     "self-service approaches that enable managers and employees to perform self-service and "
     "people management functions. "
     "Advanced HR Professionals: Evaluates, advocates for, implements and retires technology "
     "solutions to achieve HR's strategic direction, vision and goals. Evaluates and selects "
     "vendors to provide HR technology solutions. Designs and implements technology systems that "
     "optimize and integrate HR functional areas. Develops and implements technology-driven "
     "self-service approaches that enable managers and employees to perform self-service and "
     "people management functions. Assesses and implements AI-based and automation technologies "
     "that augment human talent. Collaborates with business leaders to define the role of "
     "digitalization, technology and AI in the overall business, new products or services, new "
     "markets and growth strategy."),

    # =========================================================
    # WORKPLACE KNOWLEDGE DOMAIN
    # =========================================================

    ("SHRM-6", "HRM-6.01.01", "Managing a Global Workforce",
     "All HR Professionals: Maintains up-to-date knowledge of political, economic, social, "
     "technological, legal and environmental (PESTLE) factors and their influence on an "
     "organization's universal workforce. Administers and supports HR activities associated with "
     "a global and mobile workforce. Balances the organization's desire for standardization of "
     "cross-border HR programs, practices and policies with local needs. Manages and supports the "
     "organization's immigration and mobility program in accordance with regulatory or compliance "
     "requirements. Manages the day-to-day activities associated with international (expatriate) "
     "assignments. "
     "Advanced HR Professionals: Recognizes and responds to global PESTLE issues that influence "
     "the organization's strategy and workforce. Develops a comprehensive organizational strategy "
     "that addresses global workforce issues. Consults with business leaders to define global "
     "competencies and embed them throughout the organization. Establishes and oversees the "
     "organization's immigration and mobility policy and program in accordance with regulatory or "
     "compliance requirements. Identifies opportunities to achieve efficiencies and cost savings "
     "by moving work across borders. Designs and oversees programs for international (expatriate) "
     "assignments that support the organizational strategy and workforce."),

    ("SHRM-6", "HRM-6.02.01", "Risk Management",
     "All HR Professionals: Monitors PESTLE factors and their influence on the organization. "
     "Administers and supports HR programs, practices and policies that identify and/or mitigate "
     "workplace risk. Implements crisis management, contingency and business continuity plans for "
     "the HR function and the organization. Communicates critical information about risks and risk "
     "mitigation to employees at all levels. Conducts due diligence investigations to evaluate "
     "risks and ensure legal and regulatory compliance. Conducts workplace safety- and "
     "health-related investigations. Audits risk management activities and plans. Maintains and "
     "ensures accurate reporting of internationally accepted workplace health and safety standards. "
     "Incorporates anticipated level of risk into business cases. "
     "Advanced HR Professionals: Develops, implements and oversees formal and routinized processes "
     "for monitoring the organization's internal and external environments to identify potential "
     "risks. Monitors and evaluates labor market, industry and global trends at the macro level "
     "for their impact on the organization. Examines potential threats to the organization and "
     "guides leadership accordingly. Develops, implements and oversees a comprehensive enterprise "
     "risk management strategy. Develops crisis management, contingency and business continuity "
     "plans for the HR function and the organization. Communicates critical information about "
     "risks and risk mitigation to senior-level employees and external stakeholders. Ensures that "
     "risk management activities and plans are audited and the results are used to improve risk "
     "mitigation strategies. Oversees workplace safety- and health-related investigations and "
     "reporting. Establishes strategies to address workplace retaliation and violence. Leads "
     "after-action debriefs following significant workplace incidents. Evaluates the anticipated "
     "level of risk associated with strategic opportunities."),

    ("SHRM-6", "HRM-6.03.01", "Corporate Social Responsibility",
     "All HR Professionals: Acts as a professional role model and representative of the "
     "organization when interacting with the community. Identifies and promotes opportunities for "
     "HR and the organization to engage in CSR activities that align with the organization's CSR "
     "strategy. Identifies opportunities to incorporate environmentally and socially responsible "
     "business practices and shares them with leadership. Helps staff at all levels understand "
     "the societal impact of business decisions and the role of the organization's CSR strategy "
     "in improving the community. Maintains transparency of HR programs, practices and policies, "
     "where appropriate. Coaches managers to achieve an appropriate level of transparency in "
     "organizational practices and decisions. "
     "Advanced HR Professionals: Develops a CSR strategy that reflects the organization's mission "
     "and values. Coordinates with business leaders to integrate CSR objectives throughout the "
     "organization. Coordinates with business leaders to develop and implement appropriate levels "
     "of corporate self-governance and transparency. Partners with business leaders to develop "
     "strategies that encourage and support environmentally and socially responsible business "
     "decisions. Aligns CSR activities with the organization's CSR strategy and engages the "
     "organization's workforce and the community at large. Uses metrics to measure and report how "
     "the organization's CSR programs enhance the employee value proposition, positively impact "
     "HR programs or contribute to the organization's competitive advantage."),

    ("SHRM-6", "HRM-6.04.01", "U.S. Employment Law & Regulations",
     "All HR Professionals: Maintains a current working knowledge of relevant domestic and global "
     "employment laws. Ensures that HR programs, practices and policies align and comply with laws "
     "and regulations. Coaches employees at all levels in understanding and avoiding illegal and "
     "noncompliant HR-related behaviors. Brokers internal or external legal services for "
     "interpretation of employment laws. "
     "Advanced HR Professionals: Maintains current, expert knowledge of relevant domestic and "
     "global employment laws. Establishes and monitors criteria for organizational compliance with "
     "laws and regulations. Educates and advises leadership on HR-related legal and regulatory "
     "compliance issues. Oversees fulfillment of compliance requirements for HR programs, "
     "practices and policies. Ensures that HR technologies facilitate compliance and reporting "
     "requirements."),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Remove existing SHRM data
    c.execute("SELECT id FROM competency_categories WHERE letter LIKE 'SHRM-%'")
    existing_cat_ids = [r[0] for r in c.fetchall()]
    if existing_cat_ids:
        ph = ",".join("?" * len(existing_cat_ids))
        c.execute(f"SELECT id FROM competencies WHERE category_id IN ({ph})", existing_cat_ids)
        existing_comp_ids = [r[0] for r in c.fetchall()]
        if existing_comp_ids:
            ph2 = ",".join("?" * len(existing_comp_ids))
            c.execute(f"DELETE FROM item_competency_links WHERE competency_id IN ({ph2})", existing_comp_ids)
            c.execute(f"DELETE FROM competencies WHERE id IN ({ph2})", existing_comp_ids)
        c.execute(f"DELETE FROM competency_categories WHERE id IN ({ph})", existing_cat_ids)
        print(f"Cleared {len(existing_cat_ids)} existing SHRM categories")

    # Insert categories
    cat_id_map = {}
    for letter, title in CATEGORIES:
        c.execute("INSERT INTO competency_categories (letter, title) VALUES (?, ?)", (letter, title))
        cat_id_map[letter] = c.lastrowid

    # Insert competencies
    for letter, code, name, description in COMPETENCIES:
        c.execute(
            "INSERT INTO competencies (category_id, code, name, description) VALUES (?, ?, ?, ?)",
            (cat_id_map[letter], code, name, description),
        )

    conn.commit()
    print(f"Inserted {len(CATEGORIES)} SHRM categories")
    print(f"Inserted {len(COMPETENCIES)} SHRM competencies")
    print()

    # Summary by cluster
    for letter, title in CATEGORIES:
        c.execute(
            "SELECT COUNT(*) FROM competencies WHERE category_id = ?",
            (cat_id_map[letter],),
        )
        n = c.fetchone()[0]
        print(f"  {letter} {title}: {n} competencies")

    # Verify descriptions are populated
    c.execute("""
        SELECT COUNT(*) FROM competencies
        WHERE category_id IN (SELECT id FROM competency_categories WHERE letter LIKE 'SHRM-%')
        AND (description IS NULL OR description = '')
    """)
    empty = c.fetchone()[0]
    if empty:
        print(f"\nWARNING: {empty} competencies have empty descriptions")
    else:
        print("\nAll competency descriptions populated.")

    conn.close()


if __name__ == "__main__":
    main()
