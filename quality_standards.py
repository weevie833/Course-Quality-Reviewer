"""
CQR Quality Standards — permanent fixture used as evaluation criteria.
Each standard contains a list of sub-standards with description and interpretation text.
"""

STANDARDS = {
    1: {
        "substandards": [
            {
                "id": "1.1",
                "description": "Instructions make clear how to get started and where to find various course components.",
                "interpretation": (
                    'Use the first visit to the course to experience what learners will experience. '
                    'Look for logical navigation and clear instructions for getting started. '
                    'Is it easy to access the syllabus? Is it easy to determine and find the first items '
                    'for a learner to see and do? Useful examples: Home page, "Start Here" button, '
                    'course tour, course map, scavenger hunt.'
                ),
            },
            {
                "id": "1.2",
                "description": "Learners are introduced to the purpose and structure of the course.",
                "interpretation": (
                    'Information in the syllabus or course home page or introductory module describes '
                    'the course and how learning takes place. This may include indications of delivery '
                    'modes (online asynchronous, synchronous, bi-chronous, hybrid), types of learning '
                    'activities and assessments, etc. Examples: course description, course outline, '
                    'alignment map, activity listing.'
                ),
            },
            {
                "id": "1.3",
                "description": "Communication guidelines for the course are clearly stated.",
                "interpretation": (
                    'Community guidelines or netiquette statements for learner communication are '
                    'prominently provided in the syllabus or course introduction. These describe the '
                    'methods and conduct of learner communication for the course.'
                ),
            },
            {
                "id": "1.4",
                "description": (
                    'Course and institutional policies with which the learner is expected to comply '
                    'are clearly stated within the course, or a link to current policies is provided.'
                ),
                "interpretation": (
                    'Policies for the institution and the course may include student conduct, academic '
                    'integrity, attendance, DEI, withdrawal, provisions for service members, grievances, '
                    'accessibility, etc. Institutional policies should be part of course provisioning. '
                    'Focus on course policies.'
                ),
            },
            {
                "id": "1.5",
                "description": (
                    'Minimum technology requirements for the course are clearly stated, and information '
                    'on how to obtain the technologies is provided.'
                ),
                "interpretation": (
                    'Technologies required to complete the course are clearly listed. Learners are '
                    'informed how to obtain technology and access to special learning platforms. Notice '
                    'should be enough before the required use that students can access and learn the technology.'
                ),
            },
            {
                "id": "1.6",
                "description": (
                    'Technical skills and digital information literacy skills expected of the learner '
                    'are clearly stated.'
                ),
                "interpretation": (
                    'Examples — Technical: skills with the LMS, file submission, special required '
                    'software, presentation software and platforms, collaboration software, e-mail, '
                    'video tools, etc. Digital Literacy: accessing computer networks, libraries, '
                    'academic search tools, information analysis skills, proper citations, etc.'
                ),
            },
            {
                "id": "1.7",
                "description": (
                    'Required prior knowledge in the discipline and/or any specific competencies are '
                    'clearly stated in the course site.'
                ),
                "interpretation": (
                    'Examples: Prerequisite/corequisite courses, existing credentials, expected '
                    'foundational knowledge, relevant related experience/competencies, etc.'
                ),
            },
            {
                "id": "1.8",
                "description": "The self-introduction by the instructor is welcoming and is available in the course site.",
                "interpretation": (
                    "The instructor's self-introduction is important to establish community and presence. "
                    'Recommend video, but at a minimum: photo and text introduction outlining identity, '
                    'experience, teaching philosophy, relevant research/publications, personal information '
                    'such as hobbies, family, travel, etc.'
                ),
            },
            {
                "id": "1.9",
                "description": "Learners have the opportunity to introduce themselves.",
                "interpretation": (
                    'Introductory module should have an opportunity for learners to introduce themselves '
                    'and build community. Introductions can be text or video in the discussion board, '
                    'and/or include the use of other tools (Padlet, Jamboard, etc.). Recommended: guidance '
                    'or exemplar on what information students should include in their introduction.'
                ),
            },
        ],
    },
    2: {
        "substandards": [
            {
                "id": "2.1",
                "description": "The course-level learning objectives describe outcomes that are measurable.",
                "interpretation": (
                    'Course-level Learning Objectives describe what learners will be able to do when they '
                    'have finished the course. Objectives should be concise and observable enough to be '
                    'measured. CLOs should include appropriate verbs that demonstrate varying levels of '
                    'knowledge. Check alignment with 2.2, 3.1, 4.1, 5.1, 6.1. (Alignment standard)'
                ),
            },
            {
                "id": "2.2",
                "description": (
                    'The module/unit-level learning objectives describe outcomes that are measurable and '
                    'consistent with the course-level objectives.'
                ),
                "interpretation": (
                    'Module-level learning objectives clearly describe what learners will do in specific '
                    'and observable language. Alignment to course-level objectives should be evident through '
                    'context or notation/mapping. MLOs should include appropriate verbs that demonstrate '
                    'varying levels of knowledge. Check alignment with 2.1, 3.1, 4.1, 5.1, 6.1. (Alignment standard)'
                ),
            },
            {
                "id": "2.3",
                "description": (
                    'Learning objectives are clearly stated, are learner-centered, and are prominently '
                    'located in the course.'
                ),
                "interpretation": (
                    'Learning objectives should be clearly stated: concise and without jargon or complex '
                    'language. Framing should be around what the learner will do, rather than what the '
                    'instructor will teach (learner-centered). Course-level objectives should be prominently '
                    'located in the syllabus and/or welcome module. Module-level objectives should be '
                    'prominently placed in the corresponding module or unit. Confirm that all three parts '
                    'of this standard are met (clear, learner-centered, prominent).'
                ),
            },
            {
                "id": "2.4",
                "description": (
                    'The relationship between learning objectives, learning activities, and assessments '
                    'is made clear.'
                ),
                "interpretation": (
                    'The alignment between assessments, activities and objectives should be explicit through '
                    'text, map/diagram, notation, etc. Learners should be able to visualize the connection between them.'
                ),
            },
            {
                "id": "2.5",
                "description": "The learning objectives are suited to and reflect the level of the course.",
                "interpretation": (
                    "The achievement level in the objectives is appropriate for the course level. Bloom's "
                    "or Fink's Taxonomies are useful resources. Courses should have representation across "
                    'taxonomy levels. Consult with SME if needed.'
                ),
            },
        ],
    },
    3: {
        "substandards": [
            {
                "id": "3.1",
                "description": "The assessments measure the achievement of the stated learning objectives.",
                "interpretation": (
                    "Each assessment should be aligned thematically and taxonomically (e.g., Bloom's, "
                    "Fink's) to one or more module-level objectives (construct relevance). (Alignment standard)"
                ),
            },
            {
                "id": "3.2",
                "description": (
                    'The course grading policy is stated clearly, available at the beginning of the course, '
                    'and consistent throughout the course site.'
                ),
                "interpretation": (
                    'An explanation of how grades are weighted and/or calculated is clearly presented at '
                    'the beginning of the course, including penalties for late work. The policy should be '
                    'consistent throughout the course — for instance, if the syllabus references a '
                    'points-based system, assessments should reflect grades with points, not letters or '
                    'percentages. If alternative grading (peer evaluation, ungrading, etc.) is used, that '
                    'should be made clear.'
                ),
            },
            {
                "id": "3.3",
                "description": (
                    "Specific and descriptive criteria are provided for the evaluation of learners' work, "
                    'and their connection to the course grading policy is clearly explained.'
                ),
                "interpretation": (
                    'Clear and complete criteria are provided before learners begin a particular assignment '
                    'or assessment. Checklists and/or rubrics are recommended.'
                ),
            },
            {
                "id": "3.4",
                "description": (
                    'The course includes multiple types of assessments that are sequenced and suited to '
                    'the level of the course.'
                ),
                "interpretation": (
                    'Assessments provide multiple ways for learners to demonstrate achievement (UDL). '
                    'Courses should use a variety of assessment types. Authentic assessment is encouraged. '
                    'All three parts of this specific standard (variety of types, sequenced, suited-to-level) '
                    'should be present.'
                ),
            },
            {
                "id": "3.5",
                "description": (
                    'The types and timing of assessments provide learners with multiple opportunities to '
                    'track their learning progress with timely feedback.'
                ),
                "interpretation": (
                    'Frequent lower-stakes formative assessments provide learners with opportunities for '
                    'feedback on learning progress with low penalties for poor performance. Determine whether '
                    'learners have sufficient opportunities to track progress and improve learning. Examples: '
                    'graded drafts, self-check quizzes with multiple attempts and automated feedback, '
                    'scaffolded assignments, games and assignments with built-in feedback, discussions, '
                    'peer reviews, etc.'
                ),
            },
            {
                "id": "3.6",
                "description": (
                    'The assessments provide guidance to the learner about how to uphold academic integrity.'
                ),
                "interpretation": (
                    "Assessments should reflect the institution and/or course's academic integrity policies. "
                    'Examples: essay assignment provides resources for appropriate citations, instructions '
                    'explain permitted sources, materials, and collaboration, etc.'
                ),
            },
        ],
    },
    4: {
        "substandards": [
            {
                "id": "4.1",
                "description": "The instructional materials contribute to the achievement of the stated learning objectives.",
                "interpretation": (
                    'Materials (e.g., texts and OER, publisher or instructor-created materials, slides, '
                    'lectures, videos, diagrams, images, websites) provide information or skills required '
                    'by learners to achieve objectives. Consult with SME if necessary. (Alignment standard)'
                ),
            },
            {
                "id": "4.2",
                "description": (
                    'The relationship between the use of instructional materials in the course and completion '
                    'of learning activities and assessments is clearly explained.'
                ),
                "interpretation": (
                    'Explanation of how materials prepare learners to complete learning activities and '
                    'assessments is provided in a module overview, task list, notation, or in narrative '
                    'context around the material. Relevance of required and optional instructional material '
                    'is explained. Useful examples: essay prompt indicates which module materials to be '
                    'referenced, links to external sites include explanation of the relevance of the site '
                    'to the learning activities, a quiz description indicates which chapters/modules are '
                    'relevant to the assessment.'
                ),
            },
            {
                "id": "4.3",
                "description": (
                    'The course models the academic integrity expected of learners by providing both '
                    'source references and permissions for use of instructional materials.'
                ),
                "interpretation": (
                    'Instructional materials include references and permissions where applicable. The format '
                    'of references follows the prescribed style guide. OER should include the CC license. '
                    'Learners can be directed to resources outside the LMS by hyperlink. If deep-linking, '
                    'citation is still recommended.'
                ),
            },
            {
                "id": "4.4",
                "description": "The instructional materials represent up-to-date theory and practice in the discipline.",
                "interpretation": (
                    'Review copyright/publishing dates of required materials. Question a SME about materials '
                    'that seem inappropriate or "stale." Foundational or historical concepts may often be '
                    'appropriately drawn from older material.'
                ),
            },
            {
                "id": "4.5",
                "description": "A variety of instructional materials is used in the course.",
                "interpretation": (
                    'The course makes use of a variety of materials to deliver content (text, media, etc.). '
                    'Variety may also refer to representation of different people/perspectives/cultures. '
                    'Consider UDL Representation Guideline.'
                ),
            },
        ],
    },
    5: {
        "substandards": [
            {
                "id": "5.1",
                "description": "The learning activities help learners achieve the stated objectives.",
                "interpretation": (
                    'Learning activities help learners meet objectives through interaction with the course '
                    'content, the learning community, and their instructor. Examples: class discussions, '
                    'role-playing, simulations, case studies, etc. Ensure that the activities support '
                    'relevant learner practice. (Alignment standard)'
                ),
            },
            {
                "id": "5.2",
                "description": "Learning activities provide opportunities for interactions that support active learning.",
                "interpretation": (
                    'Determine if opportunities for active learning through learner-learner, '
                    'learner-instructor, and learner-content interactions are present in the course. '
                    'For some courses, learner-learner interaction may not be required. If learner-learner '
                    'interaction is not present, consult with SME to see if such interaction is possible.'
                ),
            },
            {
                "id": "5.3",
                "description": (
                    "The instructor's plan for regular interaction with learners in substantive ways "
                    'during the course is clearly stated.'
                ),
                "interpretation": (
                    'The action plan may include: When can learners expect instructor responses to questions? '
                    'What is the turnaround time for instructor feedback on submitted work? Other examples: '
                    'are announcements posted frequently? Are there scheduled online review sessions during '
                    'the term? Is there a plan for 1-1 instructor-student interactions (check-ins, etc.)?'
                ),
            },
            {
                "id": "5.4",
                "description": "The requirements for learner interaction are clearly stated.",
                "interpretation": (
                    'Look for a clear statement regarding requirements for learner participation in course '
                    'interactions (frequency, length, timeliness, etc.). Examples: students should log in '
                    'and complete specific tasks a certain number of days per week; description of discussion '
                    'requirements and definition of "substantive post," etc.'
                ),
            },
        ],
    },
    6: {
        "substandards": [
            {
                "id": "6.1",
                "description": "The tools used in the course support the learning objectives.",
                "interpretation": (
                    'Tools should promote achievement of learning objectives without introducing excessive '
                    'construct-irrelevant learning around the tool use. Examples of tools: quizzing, '
                    'discussions, games, whiteboards, XR, web conferencing, collaboration tools. Information '
                    'is provided that makes it clear how the tools support learning objectives. Tools are '
                    'not used for their own sake. (Alignment standard)'
                ),
            },
            {
                "id": "6.2",
                "description": "Course tools promote learner engagement and active learning.",
                "interpretation": (
                    'All courses evaluated by CQR are 100% asynchronous online courses — no synchronous '
                    'or hybrid engagement is expected or required. Do NOT flag the absence of synchronous '
                    'tools (Zoom, Teams, webinars) as a gap. Evaluate only whether the asynchronous tools '
                    'present support active learning through learner-instructor, learner-content, and '
                    'learner-learner domains. Asynchronous tool examples: discussion forums, collaborative '
                    'documents, games, simulations, self-paced quizzes, multimedia content, peer review '
                    'activities, etc.'
                ),
            },
            {
                "id": "6.3",
                "description": "A variety of technology is used in the course.",
                "interpretation": (
                    'Look for evidence of the use of varied technology to ensure the course achieves '
                    'multiple means of engagement, representation, and expression (UDL). Examples may '
                    'include: videos, web conferencing, collaboration tools, simulations, self-assessment '
                    'tools with immediate feedback, software for statistical analysis, etc.'
                ),
            },
            {
                "id": "6.4",
                "description": "The course provides learners with information on protecting their data and privacy.",
                "interpretation": (
                    'A statement about institutionally provided tools, provided in course provisioning, '
                    'can identify all the tools vetted by the institution as compliant with institutional '
                    'policy. There should be links to vendor privacy policies of other tools chosen by instructors.'
                ),
            },
        ],
    },
    7: {
        "substandards": [
            {
                "id": "7.1",
                "description": (
                    'The course instructions articulate or link to a clear description of the technical '
                    'support offered and how to obtain it.'
                ),
                "interpretation": (
                    'Learners have access to technical support from within the course or LMS (this is '
                    'satisfied with the UNH implementation of Canvas). Courses with externally provided '
                    'resources should include instructions for obtaining support from the vendor. '
                    'Provided in course provisioning.'
                ),
            },
            {
                "id": "7.2",
                "description": (
                    "Course instructions articulate or link to the institution's accessibility policies "
                    'and accommodation services.'
                ),
                "interpretation": (
                    'Accessibility policies and services must be accessible to learners. Accept this standard '
                    'as Met if the syllabus, any course page, or any module content references disability '
                    'services, ADA policy, or accommodation procedures — regardless of whether the content '
                    'was authored by the instructor or provided by the institution. A reference to UNH '
                    'Student Disability Services or the Americans with Disabilities Act satisfies this standard.'
                ),
            },
            {
                "id": "7.3",
                "description": (
                    "Course instructions articulate or link to the institution's academic support services "
                    'and resources that can help learners succeed in the course.'
                ),
                "interpretation": (
                    'Learners have access to academic support services and resources from within the course '
                    'or LMS. Examples: CFAR, Library, Writing Center, guides for conducting research, '
                    'writing papers, citations, etc. Provided in course provisioning.'
                ),
            },
            {
                "id": "7.4",
                "description": (
                    "Course instructions articulate or link to the institution's student services and "
                    'resources that can help learners succeed.'
                ),
                "interpretation": (
                    'Learners have access to student support services and resources from within the course '
                    'or LMS. Examples: advising, registration, financial aid, counseling, career services, '
                    'etc. Provided in course provisioning.'
                ),
            },
        ],
    },
    8: {
        "substandards": [
            {
                "id": "8.1",
                "description": "Course navigation facilitates ease of use.",
                "interpretation": (
                    "The course's navigation strategies facilitate ease of movement through the course. "
                    'The standard is met if the navigation creates an easy path for students to follow. '
                    'Examples: consistency in layout and design, self-describing hyperlinks, underlining '
                    'only for hyperlinks, all links are functional, scaffolded projects are clearly '
                    'numbered, TOC for long documents.'
                ),
            },
            {
                "id": "8.2",
                "description": "The course design facilitates readability.",
                "interpretation": (
                    'Readability is a measure of how easy it is to read and follow content. Examples: '
                    'Heading and other styles are used and are consistent, whitespace / chunking is used '
                    'around content, activity instructions are consistent, naming conventions are '
                    'consistent, editing errors (spelling, grammar, punctuation, syntax) are minimal, '
                    'font size and style maximize readability, text/background contrast is sufficient.'
                ),
            },
            {
                "id": "8.3",
                "description": "Text in the course is accessible.",
                "interpretation": (
                    'This standard applies to text in LMS pages, files, documents, slides, etc. Text is '
                    'discoverable (selectable, searchable), hierarchical (styles), and of sufficient '
                    'contrast. Text color does not convey meaning by itself. Tables are used to organize '
                    'information/data and are set up with headings, captions, etc. Tables should not be '
                    'used merely as a formatting tool. '
                    'IMPORTANT: All courses evaluated by CQR are Canvas courses. The Canvas course template '
                    'provides the heading hierarchy (course title, module title, page title) through the LMS '
                    'shell — this structural hierarchy is NOT present in the extracted content because it is '
                    'part of the Canvas template, not instructor-authored HTML. Instructor-authored content '
                    'is written as paragraph text within that template by design. Do NOT flag the absence of '
                    'heading tags (H1, H2, H3) in extracted page or assignment content as a gap. Instead, '
                    'evaluate whether: text is selectable/not image-based, color is not the sole means of '
                    'conveying meaning, and any instructor-authored tables use proper structure.'
                ),
            },
            {
                "id": "8.4",
                "description": "Images in the course are accessible.",
                "interpretation": (
                    'Images include alt-text, long descriptions, or other means of description. '
                    'Decorative images are marked as such.'
                ),
            },
            {
                "id": "8.5",
                "description": "Video and audio content in the course is accessible.",
                "interpretation": (
                    'Video and audio content includes captions or transcripts that contain equivalent '
                    'information. Captions and transcripts are edited for accuracy. Complex diagrams or '
                    'imagery in a video should be described/transcribed.'
                ),
            },
            {
                "id": "8.6",
                "description": "Multimedia in the course is easy to use.",
                "interpretation": (
                    'Media and interactive elements are cross-platform and cross-browser. Any special '
                    'elements that are not cross-platform should be described in the technical requirements '
                    'at the start of the course. Limitations on browser incompatibility or requirements on '
                    'bandwidth should be clearly stated. Video should be of sufficient resolution and visual '
                    'quality. Audio should contain clear dialog distinguishable from background noise. '
                    'Longer videos should be broken into shorter segments.'
                ),
            },
            {
                "id": "8.7",
                "description": "Vendor accessibility statements are provided for the technologies used in the course.",
                "interpretation": (
                    'Accessibility statements for supported technologies are provided in course provisioning. '
                    'Instructor should link to accessibility statements for other technology/platforms used '
                    'in the course.'
                ),
            },
        ],
    },
}
