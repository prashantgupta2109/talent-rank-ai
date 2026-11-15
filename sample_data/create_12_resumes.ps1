Add-Type -AssemblyName System.IO.Compression.FileSystem

function New-SamplePdf {
    param(
        [string]$Path,
        [string[]]$Lines
    )

    $streamContent = "BT`n/F1 11 Tf`n50 740 Td`n14 TL`n"
    foreach ($line in $Lines) {
        $escaped = $line.Replace("\", "\\").Replace("(", "\(").Replace(")", "\)")
        $streamContent += "($escaped) '`n"
    }
    $streamContent += "ET`n"

    $streamBytes = [System.Text.Encoding]::ASCII.GetBytes($streamContent)
    $streamLen = $streamBytes.Length

    $obj4 = "4 0 obj`n<< /Length $streamLen >>`nstream`n" + $streamContent + "endstream`nendobj`n"
    $obj1 = "1 0 obj`n<< /Type /Catalog /Pages 2 0 R >>`nendobj`n"
    $obj2 = "2 0 obj`n<< /Type /Pages /Kids [3 0 R] /Count 1 >>`nendobj`n"
    $obj3 = "3 0 obj`n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>`nendobj`n"
    $obj5 = "5 0 obj`n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>`nendobj`n"

    $header = "%PDF-1.4`n"
    $offset1 = $header.Length
    $offset2 = $offset1 + $obj1.Length
    $offset3 = $offset2 + $obj2.Length
    $offset4 = $offset3 + $obj3.Length
    $offset5 = $offset4 + $obj4.Length
    $xrefOffset = $offset5 + $obj5.Length

    $xref = "xref`n0 6`n0000000000 65535 f `n" +
            ("{0:D10} 00000 n `n" -f $offset1) +
            ("{0:D10} 00000 n `n" -f $offset2) +
            ("{0:D10} 00000 n `n" -f $offset3) +
            ("{0:D10} 00000 n `n" -f $offset4) +
            ("{0:D10} 00000 n `n" -f $offset5)

    $trailer = "trailer`n<< /Size 6 /Root 1 0 R >>`nstartxref`n$xrefOffset`n%%EOF`n"

    $fullPdf = $header + $obj1 + $obj2 + $obj3 + $obj4 + $obj5 + $xref + $trailer
    [System.IO.File]::WriteAllBytes($Path, [System.Text.Encoding]::ASCII.GetBytes($fullPdf))
}

function New-SampleDocx {
    param(
        [string]$Path,
        [string[]]$Lines
    )

    $tempDir = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.Guid]::NewGuid().ToString())
    [System.IO.Directory]::CreateDirectory($tempDir) | Out-Null
    [System.IO.Directory]::CreateDirectory("$tempDir/_rels") | Out-Null
    [System.IO.Directory]::CreateDirectory("$tempDir/word") | Out-Null
    [System.IO.Directory]::CreateDirectory("$tempDir/word/_rels") | Out-Null

    $contentTypes = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' +
        '<Default Extension="xml" ContentType="application/xml"/>' +
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>' +
        '</Types>'
    [System.IO.File]::WriteAllText("$tempDir/[Content_Types].xml", $contentTypes)

    $rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>' +
        '</Relationships>'
    [System.IO.File]::WriteAllText("$tempDir/_rels/.rels", $rels)

    $wordRels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
        '</Relationships>'
    [System.IO.File]::WriteAllText("$tempDir/word/_rels/document.xml.rels", $wordRels)

    $docBody = ""
    foreach ($line in $Lines) {
        $escaped = [System.Security.SecurityElement]::Escape($line)
        $docBody += "<w:p><w:r><w:t>$escaped</w:t></w:r></w:p>"
    }

    $docXml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">' +
        '<w:body>' + $docBody + '</w:body></w:document>'
    [System.IO.File]::WriteAllText("$tempDir/word/document.xml", $docXml, [System.Text.Encoding]::UTF8)

    if (Test-Path $Path) { Remove-Item -Force $Path }
    [System.IO.Compression.ZipFile]::CreateFromDirectory($tempDir, $Path)
    Remove-Item -Recurse -Force $tempDir
}

$targetDir = "sample_data"
if (!(Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir | Out-Null }

# ==============================================================================
# 1. STRONG FIT: Dr. Alex Mercer (PDF)
# ==============================================================================
New-SamplePdf -Path "$targetDir\candidate_01_strong_alex_mercer.pdf" -Lines @(
    "Alex Mercer",
    "alex.mercer@gmail.com | (415) 555-0192 | San Francisco, CA",
    "Professional Summary:",
    "Staff Machine Learning Engineer with 6 years of expertise architecting high-throughput NLP systems and LLM pipelines.",
    "Technical Skills:",
    "Python, PyTorch, Hugging Face, Transformers, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, scikit-learn, Git",
    "Work Experience:",
    "Lead Machine Learning Engineer | NeuralScale AI | Jan 2021 - Present",
    "- Designed and deployed enterprise RAG pipeline serving 2M daily queries using FastAPI and ChromaDB vector search.",
    "- Fine-tuned open-source LLMs using PyTorch and Hugging Face on AWS EC2 clusters.",
    "Senior ML Engineer | Apex Data Labs | Mar 2018 - Dec 2020",
    "- Built real-time text classification services with scikit-learn, spaCy, and PostgreSQL.",
    "- Containerized services with Docker and orchestrated deployment via Kubernetes.",
    "Education:",
    "Ph.D. in Computer Science | Stanford University | 2018",
    "Bachelor of Science in Mathematics | UC Berkeley | 2014"
)

# ==============================================================================
# 2. STRONG FIT: Priya Sharma (DOCX)
# ==============================================================================
New-SampleDocx -Path "$targetDir\candidate_02_strong_priya_sharma.docx" -Lines @(
    "Priya Sharma",
    "priya.sharma@outlook.com | (650) 555-0143 | San Jose, CA",
    "Professional Summary:",
    "Senior AI & Python Engineer with 5.5 years of industry experience developing GenAI microservices and ML infrastructure.",
    "Technical Skills:",
    "Python, PyTorch, TensorFlow, FastAPI, scikit-learn, Docker, AWS, PostgreSQL, ChromaDB, LangChain, CI/CD",
    "Work Experience:",
    "Senior AI Engineer | CognitiveWorks | Aug 2020 - Present",
    "- Architected generative AI search systems utilizing LangChain, Hugging Face embeddings, and FastAPI.",
    "- Implemented CI/CD pipelines via GitHub Actions and deployed containerized microservices to AWS EKS.",
    "Machine Learning Engineer | DataVision Corp | Jun 2018 - Jul 2020",
    "- Developed predictive analytics models in Python and TensorFlow; optimized SQL queries on PostgreSQL.",
    "Education:",
    "Master of Science in Computer Science | Carnegie Mellon University | 2018",
    "Bachelor of Technology in Information Technology | IIT Bombay | 2016"
)

# ==============================================================================
# 3. STRONG FIT: Marcus Vance (PDF)
# ==============================================================================
New-SamplePdf -Path "$targetDir\candidate_03_strong_marcus_vance.pdf" -Lines @(
    "Marcus Vance",
    "marcus.vance@techcorp.io | (206) 555-0188 | Seattle, WA",
    "Professional Summary:",
    "Senior NLP Systems Engineer with 5 years experience specializing in semantic vector search and scalable ML APIs.",
    "Technical Skills:",
    "Python, PyTorch, Sentence Transformers, spaCy, FastAPI, Flask, Docker, AWS, PostgreSQL, SQL, Git",
    "Work Experience:",
    "Senior Machine Learning Engineer | DeepSemantic | Feb 2021 - Present",
    "- Engineered vector embedding search platform using Sentence Transformers and FAISS.",
    "- Deployed RESTful API endpoints using FastAPI and Docker containers on AWS EC2.",
    "NLP Engineer | TextLogic Solutions | Jan 2019 - Jan 2021",
    "- Created automated entity recognition pipelines using spaCy, scikit-learn, and PostgreSQL.",
    "Education:",
    "Master of Science in Data Science | University of Washington | 2018",
    "Bachelor of Science in Computer Science | Western Washington University | 2016"
)

# ==============================================================================
# 4. STRONG FIT: Elena Rostova (DOCX)
# ==============================================================================
New-SampleDocx -Path "$targetDir\candidate_04_strong_elena_rostova.docx" -Lines @(
    "Elena Rostova",
    "elena.rostova@datasphere.com | (617) 555-0112 | Boston, MA",
    "Professional Summary:",
    "Python & Machine Learning Specialist with 6 years of experience building reliable ML backends and data pipelines.",
    "Technical Skills:",
    "Python, PyTorch, scikit-learn, Hugging Face, FastAPI, Docker, Kubernetes, AWS, SQL, PostgreSQL, Linux",
    "Work Experience:",
    "Senior Machine Learning Engineer | Synthetix AI | Mar 2020 - Present",
    "- Developed distributed ML inference services handling 500 RPS using FastAPI, PyTorch, and Docker.",
    "- Automated model training workflows on AWS using PostgreSQL metadata tracking.",
    "Software Engineer - Machine Learning | Boston Analytics | Jan 2018 - Feb 2020",
    "- Built feature extraction pipelines and deployed ML models into production.",
    "Education:",
    "Master of Science in Computer Science | MIT | 2017",
    "Bachelor of Science in Software Engineering | Northeastern University | 2015"
)

# ==============================================================================
# 5. MEDIUM FIT: Daniel Kim (PDF)
# ==============================================================================
New-SamplePdf -Path "$targetDir\candidate_05_mid_daniel_kim.pdf" -Lines @(
    "Daniel Kim",
    "daniel.kim@analytics.io | (312) 555-0167 | Chicago, IL",
    "Professional Summary:",
    "Data Scientist with 3.5 years of experience in statistical analysis, tabular modeling, and exploratory data analysis.",
    "Technical Skills:",
    "Python, scikit-learn, Pandas, NumPy, SQL, PostgreSQL, Matplotlib, Git, Tableau",
    "Work Experience:",
    "Data Scientist | Horizon Insights | Jun 2021 - Present",
    "- Built customer churn and classification models using scikit-learn and Pandas.",
    "- Querying and cleaning large datasets using SQL and PostgreSQL.",
    "Junior Data Analyst | Metric Solutions | Jan 2020 - May 2021",
    "- Created automated executive dashboards and Python scripts for reporting.",
    "Education:",
    "Bachelor of Science in Statistics | University of Illinois Urbana-Champaign | 2019"
)

# ==============================================================================
# 6. MEDIUM FIT: Rachel Adams (DOCX)
# ==============================================================================
New-SampleDocx -Path "$targetDir\candidate_06_mid_rachel_adams.docx" -Lines @(
    "Rachel Adams",
    "rachel.adams@devmail.org | (512) 555-0129 | Austin, TX",
    "Professional Summary:",
    "Backend Python Developer with 4 years of solid experience in microservices and relational database architecture.",
    "Technical Skills:",
    "Python, Django, Flask, FastAPI, PostgreSQL, Docker, AWS, Redis, Git, Linux",
    "Work Experience:",
    "Backend Software Engineer | CloudScale Systems | Jan 2021 - Present",
    "- Developed REST APIs using FastAPI and Django; managed PostgreSQL database schemas and Redis caching.",
    "- Containerized services with Docker and configured AWS EC2 deployments.",
    "Junior Python Developer | WebForge Technologies | Jun 2019 - Dec 2020",
    "- Maintained legacy Flask applications and wrote SQL database queries.",
    "Education:",
    "Bachelor of Science in Computer Science | University of Texas at Austin | 2019"
)

# ==============================================================================
# 7. MEDIUM FIT: Arjun Patel (PDF)
# ==============================================================================
New-SamplePdf -Path "$targetDir\candidate_07_mid_arjun_patel.pdf" -Lines @(
    "Arjun Patel",
    "arjun.patel@mlstart.io | (408) 555-0176 | Sunnyvale, CA",
    "Professional Summary:",
    "Junior Machine Learning Engineer with 2 years of experience building modern PyTorch models and FastAPI services.",
    "Technical Skills:",
    "Python, PyTorch, Hugging Face, scikit-learn, FastAPI, Docker, SQL, Git",
    "Work Experience:",
    "Junior ML Engineer | NextGen Intelligence | Jul 2022 - Present",
    "- Fine-tuned sentence transformer models and built semantic search microservices using FastAPI.",
    "- Containerized ML testing environments with Docker.",
    "Education:",
    "Master of Science in Computer Science | San Jose State University | 2022",
    "Bachelor of Science in Computer Engineering | Mumbai University | 2020"
)

# ==============================================================================
# 8. MEDIUM FIT: Chloe Bennett (DOCX)
# ==============================================================================
New-SampleDocx -Path "$targetDir\candidate_08_mid_chloe_bennett.docx" -Lines @(
    "Chloe Bennett",
    "chloe.bennett@datapipeline.net | (303) 555-0154 | Denver, CO",
    "Professional Summary:",
    "Data Engineer with 4 years of experience building scalable ETL pipelines, data warehouses, and streaming infrastructure.",
    "Technical Skills:",
    "Python, Apache Spark, Apache Airflow, Apache Kafka, SQL, PostgreSQL, Docker, AWS, Git",
    "Work Experience:",
    "Data Engineer | StreamData Tech | Mar 2021 - Present",
    "- Built automated ETL workflows using Apache Airflow and PySpark for 10TB+ daily datasets.",
    "- Designed data lake tables and optimized SQL queries in PostgreSQL and Snowflake.",
    "Data Analyst | Frontier Analytics | Jan 2020 - Feb 2021",
    "- Wrote Python automation scripts and SQL queries for business reporting.",
    "Education:",
    "Bachelor of Science in Information Technology | University of Colorado Boulder | 2019"
)

# ==============================================================================
# 9. WEAK FIT: Lucas Silva (PDF)
# ==============================================================================
New-SamplePdf -Path "$targetDir\candidate_09_weak_lucas_silva.pdf" -Lines @(
    "Lucas Silva",
    "lucas.silva@frontcraft.com | (212) 555-0138 | New York, NY",
    "Professional Summary:",
    "Senior Frontend Developer with 5 years experience creating responsive, high-performance web applications.",
    "Technical Skills:",
    "React, JavaScript, TypeScript, Next.js, HTML, CSS, Tailwind CSS, Redux, Jest, Figma",
    "Work Experience:",
    "Senior Frontend Engineer | PixelCraft Studio | Jan 2021 - Present",
    "- Led development of responsive SaaS user interfaces using React, Next.js, and Tailwind CSS.",
    "- Improved Core Web Vitals and client-side rendering performance by 40%.",
    "Frontend Developer | Metro Web Agency | Jan 2019 - Dec 2020",
    "- Built web dashboards using React, Redux, and CSS3.",
    "Education:",
    "Bachelor of Arts in Graphic Design & Web Media | New York University | 2018"
)

# ==============================================================================
# 10. WEAK FIT: Vikram Malhotra (DOCX)
# ==============================================================================
New-SampleDocx -Path "$targetDir\candidate_10_weak_vikram_malhotra.docx" -Lines @(
    "Vikram Malhotra",
    "vikram.malhotra@enterprisejava.com | (732) 555-0199 | Edison, NJ",
    "Professional Summary:",
    "Senior Enterprise Java Architect with 7 years of experience in legacy banking and financial systems.",
    "Technical Skills:",
    "Java, Spring Boot, Oracle Database, SQL, Apache Maven, JUnit, Jenkins, Linux",
    "Work Experience:",
    "Senior Java Developer | Global Core Banking | Mar 2019 - Present",
    "- Built resilient transactional banking backends using Java and Spring Boot.",
    "- Maintained legacy stored procedures on Oracle Database.",
    "Software Engineer | Premier Financial | Jan 2017 - Feb 2019",
    "- Maintained enterprise Java EE services and XML data transformations.",
    "Education:",
    "Bachelor of Engineering in Computer Science | Pune University | 2016"
)

# ==============================================================================
# 11. WEAK FIT: Sarah Jenkins (PDF)
# ==============================================================================
New-SamplePdf -Path "$targetDir\candidate_11_weak_sarah_jenkins.pdf" -Lines @(
    "Sarah Jenkins",
    "sarah.jenkins@hrpeople.com | (404) 555-0122 | Atlanta, GA",
    "Professional Summary:",
    "Technical Recruiter & People Operations Specialist with 4 years experience leading talent acquisition.",
    "Technical Skills:",
    "Technical Recruiting, Sourcing, Applicant Tracking Systems, Greenhouse, LinkedIn Recruiter, HR Policies",
    "Work Experience:",
    "Senior Technical Recruiter | TalentPeak Inc | Feb 2021 - Present",
    "- Managed end-to-end recruitment lifecycle for software engineering and executive leadership roles.",
    "HR Coordinator | Southern Enterprise Services | Jan 2020 - Jan 2021",
    "- Coordinated onboarding and employee records management.",
    "Education:",
    "Bachelor of Science in Human Resources Management | Georgia State University | 2019"
)

# ==============================================================================
# 12. WEAK FIT: David Miller (DOCX)
# ==============================================================================
New-SampleDocx -Path "$targetDir\candidate_12_weak_david_miller.docx" -Lines @(
    "David Miller",
    "david.miller@salesgrowth.io | (704) 555-0185 | Charlotte, NC",
    "Professional Summary:",
    "Senior Enterprise Account Executive with 6 years experience in B2B SaaS sales and software revenue expansion.",
    "Technical Skills:",
    "Enterprise Sales, B2B Sales, Salesforce, CRM, Contract Negotiation, SaaS Sales, Lead Generation",
    "Work Experience:",
    "Enterprise Account Executive | SaaSVelocity | Jan 2020 - Present",
    "- Closed $4.2M in annual recurring revenue selling enterprise cloud subscriptions.",
    "Sales Development Representative | Apex Software | Jan 2018 - Dec 2019",
    "- Managed inbound enterprise qualification and outbound sales cadences.",
    "Education:",
    "Bachelor of Business Administration in Marketing | UNC Charlotte | 2017"
)

Write-Host "Successfully generated 12 sample resumes (6 PDF, 6 DOCX) in $targetDir"
