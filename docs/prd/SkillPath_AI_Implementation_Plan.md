# SkillPath AI --- Complete Implementation Plan

## 0. Purpose of This Document

This document is the **implementation playbook** for the project defined
in:

**`AI-Learning-Path-Recommender-PRD.pdf`**

The PRD is the source of truth for the product scope, architecture,
requirements, algorithms, evaluation targets, technology stack, and
research contribution.

The project should be built incrementally. Do **not** attempt to
implement all advanced features at once.

The intended progression is:

``` text
Foundation
   ↓
Employee Profile
   ↓
Resume/JD Skill Extraction
   ↓
Skill Taxonomy
   ↓
Evidence-Based Skill Profile
   ↓
Skill-Gap Engine
   ↓
Course/Project/Mentor Recommendation
   ↓
Knowledge Graph
   ↓
Prerequisite-Aware Learning Path
   ↓
OR-Tools Optimization
   ↓
Assessments
   ↓
Adaptive Re-optimization
   ↓
Explainability
   ↓
RAG Learning Assistant
   ↓
GitHub Evidence
   ↓
What-If Simulation
   ↓
Skill Digital Twin
   ↓
Evaluation + Deployment
```

The PRD defines a 10-phase, 20-week roadmap, beginning with Foundation
and ending with Evaluation & Deployment. The plan below expands those
phases into concrete development tasks, checkpoints, tests, and
deliverables.

------------------------------------------------------------------------

# 1. Project North Star

## 1.1 Product

**SkillPath AI**

An evidence-based, prerequisite-aware, adaptive learning-path
recommender for employee competency development.

## 1.2 Core Loop

``` text
Employee Evidence
      ↓
Current Skill Profile
      ↓
Target Role / Job Description
      ↓
Required Skill Profile
      ↓
Weighted Skill Gaps
      ↓
Prerequisite Graph
      ↓
Course + Project + Mentor Candidates
      ↓
Hybrid Recommendation
      ↓
Optimized Learning Path
      ↓
Learning + Assessment
      ↓
New Evidence
      ↓
Updated Skill Profile
      ↓
Re-optimized Path
```

## 1.3 What Must NOT Happen

Do not reduce the project to:

``` text
Resume → LLM → "Here are some courses"
```

The PRD explicitly positions the LLM as an assistance/explanation
component. Core decisions should come from deterministic, ML, graph,
ranking, and optimization components.

------------------------------------------------------------------------

# 2. Source-of-Truth Rules for Cursor

When implementing this repository, Cursor must:

1.  Read the complete PRD before making architectural decisions.
2.  Preserve the terminology used by the PRD.
3.  Treat the PRD's functional requirements and formulas as
    authoritative.
4.  Implement the MVP first.
5.  Implement one phase at a time.
6.  Never silently remove a PRD feature because it is inconvenient.
7.  If a PRD requirement is ambiguous, document the ambiguity and choose
    the smallest implementation that preserves the intent.
8.  Keep advanced features behind modular interfaces so they can be
    added without rewriting the MVP.
9.  Write tests with every feature.
10. Update documentation after each phase.
11. Never use an LLM as the sole recommendation engine.
12. Keep recommendation explanations grounded in actual
    scoring/evidence.
13. Never present inferred skills as facts; expose confidence and
    evidence.
14. Keep privacy/security requirements in the design from the beginning.
15. Avoid premature microservice deployment complexity. The codebase can
    remain a modular monorepo while preserving service boundaries.

------------------------------------------------------------------------

# 3. Recommended Implementation Strategy

## Stage A --- Working MVP

Build this first:

``` text
Authentication
+
Employee Profile
+
Resume Upload
+
Basic Skill Extraction
+
Skill Taxonomy
+
Target Role
+
Basic Skill Gap
+
Content-Based Course Recommendation
+
Topological Learning Path
+
Basic Dashboard
```

At the end of Stage A, the application must demonstrate:

``` text
Upload Resume
      ↓
Extract Skills
      ↓
Select ML Engineer
      ↓
Calculate Gaps
      ↓
Recommend Courses
      ↓
Generate Ordered Learning Path
```

Only after this works end-to-end should advanced research components be
introduced.

## Stage B --- Research Core

Add:

-   Multi-source evidence
-   Confidence-weighted proficiency
-   Neo4j knowledge graph
-   Semantic similarity
-   Hybrid recommendation
-   Projects
-   Mentors
-   OR-Tools optimization
-   Explainability

## Stage C --- Adaptive Intelligence

Add:

-   Assessments
-   Progress tracking
-   Adaptive re-optimization
-   GitHub evidence
-   RAG assistant
-   What-if simulation
-   Skill digital twin

## Stage D --- Research Evaluation

Add:

-   Baselines
-   Ablation studies
-   Offline evaluation
-   User evaluation
-   Performance tests
-   Research documentation
-   Final deployment

------------------------------------------------------------------------

# 4. Phase 0 --- Repository Bootstrap

## Goal

Create a clean, reproducible development environment.

## Tasks

### 4.1 Initialize repository

Create:

``` text
skillpath-ai/
```

Initialize Git.

Create:

``` text
README.md
.gitignore
.env.example
LICENSE
docker-compose.yml
```

### 4.2 Create root structure

Use the PRD structure:

``` text
skillpath-ai/
├── frontend/
├── backend/
├── ml/
├── recommendation/
├── knowledge_graph/
├── optimization/
├── llm/
├── database/
├── datasets/
├── tests/
├── docs/
└── scripts/
```

### 4.3 Backend environment

Use:

-   Python 3.11
-   FastAPI
-   Pydantic
-   SQLAlchemy
-   Alembic
-   pytest
-   Ruff
-   Black
-   mypy

### 4.4 Frontend environment

Use:

-   React
-   TypeScript
-   Tailwind CSS
-   React Query
-   Zustand
-   Recharts or D3

### 4.5 Development conventions

Define:

-   Naming conventions
-   API versioning
-   Error format
-   Logging format
-   Environment variable strategy
-   Commit conventions
-   Branch strategy

## Definition of Done

-   Frontend starts successfully.
-   Backend starts successfully.
-   `/health` works.
-   Database container starts.
-   Git repository is initialized.
-   `.env.example` documents required variables.
-   README contains setup instructions.

------------------------------------------------------------------------

# 5. Phase 1 --- Foundation

## Goal

Implement authentication, employee profiles, PostgreSQL persistence, and
basic application navigation.

## 5.1 Database

Start with PostgreSQL.

Initial entities:

``` text
User
Employee
Education
WorkExperience
Skill
EmployeeSkill
Role
RoleSkill
```

Do not create every advanced table yet.

## 5.2 Authentication

Implement:

-   Registration
-   Login
-   Password hashing
-   JWT authentication
-   Current-user endpoint
-   Role-based authorization

Initial roles:

``` text
EMPLOYEE
MANAGER
MENTOR
HR_ADMIN
SYSTEM_ADMIN
```

## 5.3 Employee Profile API

Create endpoints such as:

``` text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/employees/me
PUT    /api/v1/employees/me
POST   /api/v1/employees/me/education
POST   /api/v1/employees/me/experience
```

## 5.4 Frontend

Create:

``` text
/login
/register
/dashboard
/profile
```

## Testing

Write:

-   Authentication unit tests
-   Authorization tests
-   Profile CRUD tests
-   Validation tests
-   API integration tests

## Definition of Done

A user can:

``` text
Register
→ Login
→ View profile
→ Edit profile
→ Add education
→ Add experience
→ Add skills
→ Select target role
```

------------------------------------------------------------------------

# 6. Phase 2 --- Skill Taxonomy

## Goal

Create the normalized vocabulary that every later component uses.

## Why This Is Critical

Without normalization:

``` text
ML
Machine Learning
machine-learning
MachineLearning
```

could become four different skills.

The taxonomy must map them to one canonical skill.

## Skill model

Recommended fields:

``` text
id
name
canonical_name
description
category
aliases
difficulty
```

## Example

``` text
Canonical:
Machine Learning

Aliases:
ML
machine learning
machine-learning

Category:
Artificial Intelligence
```

## Initial taxonomy

Create a practical seed dataset covering:

-   Programming
-   Data Science
-   Machine Learning
-   Deep Learning
-   NLP
-   GenAI
-   Databases
-   Cloud
-   DevOps
-   MLOps
-   Software Engineering

Do not attempt to build an enormous taxonomy before the pipeline works.

## Definition of Done

Every extracted skill can be mapped to:

``` text
skill_id
canonical_name
confidence
```

------------------------------------------------------------------------

# 7. Phase 3 --- Resume Processing and Skill Extraction

## Goal

Convert an uploaded resume into structured evidence.

## Pipeline

``` text
Resume
 ↓
Text Extraction
 ↓
Cleaning
 ↓
Section Segmentation
 ↓
Skill Detection
 ↓
Normalization
 ↓
Taxonomy Mapping
 ↓
Proficiency Estimation
 ↓
Confidence
 ↓
Evidence Record
```

## 7.1 File processing

Support:

-   PDF
-   DOCX
-   TXT

Use appropriate extraction libraries.

## 7.2 Skill extraction

Implement in layers.

### Layer 1 --- Dictionary matching

Fast baseline.

### Layer 2 --- Context-aware NLP

spaCy NER/custom processing where useful.

### Layer 3 --- Semantic matching

Sentence Transformers for ambiguous skill mentions.

### Layer 4 --- Optional LLM fallback

Use only for difficult/ambiguous cases.

## 7.3 Normalization

Examples:

``` text
ML → Machine Learning
NLP → Natural Language Processing
DL → Deep Learning
K8s → Kubernetes
```

## 7.4 Evidence output

Each extracted skill should produce:

``` json
{
  "skill_id": "...",
  "skill_name": "Python",
  "proficiency": 4.0,
  "confidence": 0.84,
  "source": "RESUME",
  "evidence_snippet": "Developed Python applications..."
}
```

## 7.5 Proficiency estimation

Initially use deterministic rules:

-   Explicit expert language
-   Years of experience
-   Frequency of mention
-   Section context
-   Project context

Do not pretend this is ground-truth proficiency.

Always expose uncertainty.

## Evaluation

Create a manually labeled test set.

Measure:

``` text
Precision
Recall
F1
```

Target from the PRD:

``` text
F1 ≥ 0.85
```

The MVP can initially target a lower threshold while improving toward
the PRD target.

------------------------------------------------------------------------

# 8. Phase 4 --- Target Role and Job Description Analysis

## Goal

Convert the target role into a structured competency profile.

## Inputs

Either:

``` text
Existing Role
```

or:

``` text
Uploaded/Pasted Job Description
```

## Output

``` json
{
  "role": "ML Engineer",
  "skills": [
    {
      "skill": "Python",
      "required_level": 4,
      "importance": 1.0
    }
  ]
}
```

## Required/preferred weights

Use the PRD starting values:

``` text
Required = 1.0
Preferred = 0.6
Mentioned = 0.4
```

These should be configurable.

## Role catalog

Seed roles such as:

``` text
Data Scientist
ML Engineer
Data Analyst
Data Engineer
Backend Engineer
AI Engineer
NLP Engineer
GenAI Engineer
MLOps Engineer
```

## Definition of Done

The system can produce a structured target skill profile from:

``` text
Role selection
OR
Job description
```

------------------------------------------------------------------------

# 9. Phase 5 --- Evidence-Based Skill Profile

## Goal

Move from self-declared skills to multi-source evidence.

## Evidence sources

The PRD identifies:

``` text
Resume
GitHub
Completed Course
Assessment
Project
Certification
Work Experience
Self Declaration
```

## Evidence model

Use:

``` text
Evidence
├── employee_id
├── skill_id
├── source_type
├── source_id
├── raw_text
├── extracted_level
├── reliability
├── recency
├── strength
└── timestamp
```

## Reliability

Use configurable source reliability.

The PRD gives self-declaration the lowest reliability and stronger
structured evidence higher reliability.

Do not hard-code the values throughout the application.

Create a configuration table or configuration module.

## Confidence formula

Implement the PRD model:

``` text
C(s) = 1 - Π(1 - r_e × σ_e × ρ_e)
```

where:

``` text
r = reliability
σ = evidence strength
ρ = recency
```

## Proficiency aggregation

Use weighted evidence:

``` text
w_e = r_e × σ_e × ρ_e

L_cur(s) =
Σ(w_e × l_e) / Σ(w_e)
```

## Conflicting evidence

Implement:

``` text
High variance
→ flag conflict
→ recommend assessment
→ show evidence in UI
```

## Definition of Done

The system can answer:

``` text
What is the employee's estimated Python level?
Why?
What evidence supports it?
How confident are we?
Is evidence conflicting?
```

------------------------------------------------------------------------

# 10. Phase 6 --- Skill Gap Engine

## Goal

Calculate and rank the employee's competency gaps.

## Basic model

``` text
Gap_basic(s) = L_required(s) - L_current(s)
```

Clamp negative values to zero.

## Enhanced model

Implement the PRD formula:

``` text
Gap(s) =
max(0, L_req - L_cur)
× I(s)
× C(s)
× R(s)
× E(s)
```

where:

``` text
I = role importance
C = confidence
R = role criticality
E = evidence strength
```

## Gap categories

Use the PRD thresholds:

``` text
Critical: Gap > 2.0
High:     1.0 < Gap ≤ 2.0
Medium:   0.5 < Gap ≤ 1.0
Low:      0 < Gap ≤ 0.5
None:     Gap = 0
```

## API

Example:

``` text
GET /api/v1/gap-analysis
```

Return:

``` json
{
  "target_role": "ML Engineer",
  "gaps": [
    {
      "skill": "Deep Learning",
      "required": 4,
      "current": 0,
      "gap": 3.2,
      "priority": "CRITICAL"
    }
  ]
}
```

## UI

Create:

-   Skill gap cards
-   Bar chart
-   Radar chart
-   Priority list
-   Current vs required level
-   Confidence indicator

## Evaluation

Use ranking metrics such as:

``` text
NDCG@10
```

------------------------------------------------------------------------

# 11. Phase 7 --- Course, Project, and Mentor Data

## Goal

Create the resource ecosystem.

## Course dataset

Fields:

``` text
id
title
provider
description
skills
difficulty
duration_hours
format
url
rating
```

## Project dataset

Fields:

``` text
id
title
description
skills
difficulty
duration_hours
technologies
deliverables
```

## Mentor dataset

Fields:

``` text
id
name
expertise
experience
availability
domains
```

## Important

Do not hard-code resources inside recommendation functions.

Resources belong in databases/datasets.

## Seed realistic data

Start with enough data to demonstrate meaningful ranking.

------------------------------------------------------------------------

# 12. Phase 8 --- Baseline Recommendation Engine

## Goal

Create a simple recommendation baseline before implementing the full
hybrid system.

This is important for research evaluation.

Implement:

``` text
Popularity baseline
Content-based baseline
Semantic baseline
```

## Content-based

Represent employee gaps and resource skills as vectors.

Use:

``` text
cosine_similarity(user_vector, resource_vector)
```

## Semantic

Use Sentence Transformers.

Initial model:

``` text
all-MiniLM-L6-v2
```

Potential later experiment:

``` text
all-mpnet-base-v2
```

## Candidate retrieval

Retrieve candidates addressing:

``` text
Top skill gaps
```

Do not compare every resource against every employee if unnecessary.

------------------------------------------------------------------------

# 13. Phase 9 --- Knowledge Graph

## Goal

Introduce Neo4j as the structural backbone for skills and dependencies.

## Node types

At minimum:

``` text
Employee
Skill
Course
Project
Mentor
TargetRole
Assessment
Certification
```

## Relationships

Implement the PRD relationships:

``` text
REQUIRES
PREREQUISITE_OF
RELATED_TO
TEACHES
PRACTICES
EXPERT_IN
RECOMMENDED_FOR
PART_OF
COMPLEMENTS
HAS_SKILL
COMPLETED
MENTORS
```

## First important graph

Build the skill prerequisite DAG.

Example:

``` text
Statistics
    ↓
Machine Learning
    ↓
Deep Learning
    ↓
Transformers
    ↓
LLMs
    ↓
RAG
```

## Graph queries

Implement:

``` text
Find prerequisites of a skill
Find courses teaching a skill
Find projects practicing a skill
Find mentors for gap skills
Find prerequisite chains
```

## Critical validation

The graph must not contain invalid cycles in the prerequisite graph.

Run cycle detection.

------------------------------------------------------------------------

# 14. Phase 10 --- Hybrid Recommendation Engine

## Goal

Combine independent recommendation signals.

The PRD defines seven major signals:

``` text
1. Semantic similarity
2. Skill-gap relevance
3. Prerequisite fit
4. Difficulty fit
5. User preference
6. Collaborative filtering
7. Knowledge graph reasoning
```

## Architecture

``` text
Candidate Retrieval
        ↓
 ┌──────┼───────┬────────┐
 ↓      ↓       ↓        ↓
Semantic Gap     KG       Difficulty
 ↓      ↓       ↓        ↓
Preference + Collaborative
        ↓
Hybrid Scoring
        ↓
Ranking
        ↓
Explainability
```

## Scoring

Implement components independently first.

Then:

``` text
Score =
w1*Semantic
+w2*Gap
+w3*Prerequisite
+w4*Difficulty
+w5*Preference
+w6*Collaborative
+w7*KG
```

Keep weights configurable.

Do not hide them inside the code.

## Research requirement

Save each component score.

Example:

``` json
{
  "semantic": 0.82,
  "gap": 0.95,
  "prerequisite": 1.0,
  "difficulty": 0.85,
  "preference": 0.70,
  "collaborative": 0.45,
  "kg": 0.90,
  "final": 0.86
}
```

This is essential for explainability and ablation studies.

------------------------------------------------------------------------

# 15. Phase 11 --- Project Recommendation

## Goal

Connect learning to hands-on practice.

For each major gap:

``` text
Skill
 ↓
Course
 ↓
Project
 ↓
Assessment
```

Example:

``` text
RAG
 ↓
RAG Fundamentals
 ↓
Document Q&A System
 ↓
RAG Assessment
```

Project ranking should consider:

-   Skills addressed
-   Gap priority
-   Difficulty
-   Current proficiency
-   Duration
-   Technologies
-   Target role

------------------------------------------------------------------------

# 16. Phase 12 --- Mentor Recommendation

## Goal

Match learners with suitable mentors.

## Matching signals

Use:

``` text
Skill overlap
Domain overlap
Experience
Availability
Learning goals
Mentor workload
```

Example:

``` text
Mentor expertise:
RAG, LLMs, Vector DBs

Learner gaps:
RAG, LLMs, Vector DBs, MLOps

Overlap:
3 major gaps
```

## Explainability

Return:

``` text
Why this mentor?

3 of your top 5 skill gaps match the mentor's expertise.
The mentor has 4 available sessions/month.
```

------------------------------------------------------------------------

# 17. Phase 13 --- Prerequisite-Aware Learning Path

## Goal

Generate a sequence rather than a list.

## Step 1

Take top skill gaps.

## Step 2

Expand prerequisite graph.

## Step 3

Identify missing foundations.

## Step 4

Construct a DAG.

## Step 5

Topologically sort.

## Step 6

Map skills to learning resources.

Example:

``` text
Statistics
 ↓
Machine Learning
 ↓
Deep Learning
 ↓
Transformers
 ↓
LLMs
 ↓
RAG
```

## Important

A prerequisite must never appear after the skill that depends on it.

Add automated validation:

``` text
prerequisite_violation_count == 0
```

------------------------------------------------------------------------

# 18. Phase 14 --- Learning Path Optimization

## Goal

Move from graph ordering to constrained optimization.

Use OR-Tools.

## Inputs

``` text
Skill gaps
Prerequisites
Course durations
Project durations
Assessment durations
Weekly availability
Deadline
Difficulty
```

## Objective

Conceptually:

``` text
Maximize:
    Skill Coverage
  + Role Relevance
  + Progress

Minimize:
    Learning Time
  + Unnecessary Content
  + Constraint Violations
```

## Constraints

Examples:

``` text
Prerequisites must be completed first.

Weekly learning hours <= employee availability.

Total learning time <= deadline.

A resource cannot be selected twice.

Required skills must receive sufficient coverage.
```

## Output

``` text
Ordered resources
+
Milestones
+
Estimated completion
+
Skill coverage
```

## Compare algorithms

For research:

``` text
Greedy
vs
Topological ordering
vs
OR-Tools optimization
```

Measure:

-   Total time
-   Skill coverage
-   Constraint violations
-   Path efficiency

------------------------------------------------------------------------

# 19. Phase 15 --- Learning Path UI

## Goal

Make the recommendation understandable.

Create a visual timeline:

``` text
FOUNDATION
──────────────
Statistics
Course
Project
Assessment

CORE ML
──────────────
Machine Learning
Course
Project
Assessment

DEEP LEARNING
──────────────
...
```

Every item should show:

-   Duration
-   Skill addressed
-   Difficulty
-   Completion status
-   Why it exists in the path

------------------------------------------------------------------------

# 20. Phase 16 --- Assessment Engine

## Goal

Verify skill acquisition.

## Assessment types

Implement progressively:

1.  MCQ
2.  Conceptual
3.  Coding
4.  Practical/project

## Assessment model

``` text
Assessment
Question
Skill
Attempt
Answer
Score
```

## Skill update

After assessment:

``` text
Assessment
 ↓
Evidence
 ↓
Updated proficiency
 ↓
Updated confidence
 ↓
Updated gap
 ↓
Path re-evaluation
```

Do not directly overwrite historical skill evidence.

Add new evidence instead.

------------------------------------------------------------------------

# 21. Phase 17 --- Adaptive Learning

## Goal

Make the path dynamic.

Example:

``` text
Assessment = 55%
        ↓
Skill not mastered
        ↓
Add refresher
        ↓
Delay dependent skill
        ↓
Re-optimize
```

If:

``` text
Assessment = 90%
```

then:

``` text
Skill satisfied
        ↓
Skip basic content
        ↓
Move to advanced content
```

## Re-optimization triggers

-   Assessment result
-   Course completion
-   Project completion
-   New GitHub evidence
-   Manual skill update
-   Mentor feedback

------------------------------------------------------------------------

# 22. Phase 18 --- Deterministic Explainability

## Goal

Every recommendation must have an auditable reason.

## Do NOT do this

``` text
LLM:
"I think this course would be great for you..."
```

## Instead

Generate an explanation from actual values:

``` text
Recommended because:

1. Addresses Deep Learning gap.
2. Gap priority = Critical.
3. Semantic similarity = 0.89.
4. Prerequisites are satisfied.
5. Difficulty matches learner level.
6. Learner prefers video courses.
```

Then optionally allow an LLM to turn those facts into natural language.

## Store explanation data

Every recommendation should retain:

``` text
score components
evidence
matched skills
gap addressed
prerequisites
ranking position
```

------------------------------------------------------------------------

# 23. Phase 19 --- RAG Learning Assistant

## Goal

Create a learning assistant grounded in the employee's context.

The assistant should know:

``` text
Current skill profile
Target role
Skill gaps
Learning path
Completed content
Current topic
Assessment results
```

## Architecture

``` text
User Question
     ↓
Context Retrieval
     ↓
Employee Profile
Learning Path
Knowledge Base
     ↓
Prompt
     ↓
LLM
     ↓
Answer
```

## Use cases

``` text
"What should I learn next?"
"Why do I need statistics?"
"Explain transformers."
"Give me a project for RAG."
"Why was this course recommended?"
```

## Guardrails

The assistant must not invent employee data.

It should say when information is unavailable.

------------------------------------------------------------------------

# 24. Phase 20 --- GitHub Evidence Integration

## Goal

Use real project evidence to improve skill confidence.

Analyze:

-   Repository languages
-   Dependencies
-   README
-   Project descriptions
-   Commit activity
-   Relevant files
-   Technology usage

## Pipeline

``` text
GitHub
 ↓
Repositories
 ↓
Technology extraction
 ↓
Skill mapping
 ↓
Evidence
 ↓
Confidence update
```

## Important

GitHub activity is evidence, not absolute proof of proficiency.

Use confidence and strength scores.

------------------------------------------------------------------------

# 25. Phase 21 --- What-If Career Simulation

## Goal

Allow learners to compare target competency profiles.

Example:

``` text
Current profile
       ↓
 ┌─────┼────────┐
 ↓     ↓        ↓
ML     NLP      GenAI
Engineer Engineer Engineer
```

For each target:

-   Skill coverage
-   Missing skills
-   Learning path
-   Estimated effort
-   Required projects
-   Mentor coverage

Do not make employment or hiring predictions.

------------------------------------------------------------------------

# 26. Phase 22 --- Skill Digital Twin

## Goal

Create a visual representation of competency state.

For each skill display:

``` text
Current Level
Required Level
Gap
Confidence
Evidence
Progress
Trend
```

Example:

``` text
Machine Learning

Current: 3.2 / 5
Required: 4.0 / 5
Gap: 0.8
Confidence: 0.91

Evidence:
Resume ✓
GitHub ✓
Assessment ✓
Project ✓
```

Add historical progress.

------------------------------------------------------------------------

# 27. Phase 23 --- Manager and HR Analytics

## Goal

Implement the organizational side after the learner flow is stable.

Manager:

``` text
Team skill heatmap
Top skill gaps
Training priorities
Learning progress
```

HR/L&D:

``` text
Role competency frameworks
Organization skill distribution
Program participation
Aggregate skill gaps
```

Privacy requirements from the PRD must be respected.

Do not expose individual employee data unnecessarily.

------------------------------------------------------------------------

# 28. Phase 24 --- Frontend Polish

## Main screens

Implement:

``` text
Login
Register
Dashboard
Profile
Resume Upload
Skill Profile
Skill Gap Analysis
Role Explorer
Course Recommendations
Project Recommendations
Mentor Recommendations
Learning Path
Assessments
Progress
AI Assistant
What-If Simulation
Skill Digital Twin
Manager Dashboard
Admin Dashboard
```

## UX principles

Every important recommendation should have:

``` text
Why?
```

button.

Show:

``` text
Confidence
Evidence
Skill gap
Expected benefit
Difficulty
Duration
```

Avoid information overload.

------------------------------------------------------------------------

# 29. Phase 25 --- API Hardening

## Requirements

Use:

-   Pydantic validation
-   Consistent error responses
-   Authentication
-   Authorization
-   Pagination
-   Filtering
-   Sorting
-   API versioning
-   OpenAPI documentation

## Example

``` text
/api/v1/recommendations/courses
/api/v1/recommendations/projects
/api/v1/recommendations/mentors
/api/v1/learning-paths
/api/v1/assessments
```

------------------------------------------------------------------------

# 30. Phase 26 --- Testing Strategy

Testing must happen continuously, not only at the end.

## Unit tests

Test:

-   Skill normalization
-   Gap calculation
-   Evidence aggregation
-   Confidence calculation
-   Recommendation components
-   Graph traversal
-   Topological sort
-   Optimization constraints

## Integration tests

Test:

``` text
Resume → Skill Profile
Skill Profile → Gap
Gap → Recommendations
Recommendations → Path
Assessment → Profile update
Profile update → Reoptimization
```

## End-to-end test

Automate:

``` text
Register
→ Upload resume
→ Select role
→ Analyze gaps
→ Generate recommendations
→ Generate path
→ Complete assessment
→ Update path
```

## Performance tests

Measure PRD targets:

``` text
API p95 < 500ms
Skill extraction < 10s
Gap analysis < 2s
Path generation < 3s
Recommendation < 1s
Page load < 2s
```

------------------------------------------------------------------------

# 31. Research Evaluation

This section is mandatory if the project is intended for a research
paper.

## 31.1 Recommendation baselines

Compare:

``` text
1. Popularity
2. Content-based
3. Semantic
4. Knowledge graph
5. Proposed hybrid
```

## 31.2 Metrics

Use:

``` text
Precision@K
Recall@K
NDCG@K
MAP@K
Coverage
Diversity
```

## 31.3 Skill extraction

Measure:

``` text
Precision
Recall
F1
```

## 31.4 Skill-gap ranking

Measure:

``` text
NDCG@10
```

## 31.5 Learning path

Measure:

``` text
Prerequisite violations
Skill coverage
Total learning time
Path efficiency
```

## 31.6 Explainability

User study:

``` text
Was the reason understandable?
Was it useful?
Did it match the recommendation?
```

## 31.7 Ablation study

Remove one signal at a time:

``` text
Full model

- Semantic
- Gap relevance
- Prerequisite
- Difficulty
- Preference
- Collaborative
- KG
```

Measure performance change.

This is important for demonstrating whether each component actually
contributes.

------------------------------------------------------------------------

# 32. Data Strategy

If real employee data is unavailable:

Use a combination of:

``` text
Public skill taxonomies
+
Public course/resource metadata
+
Synthetic employee profiles
+
Synthetic interaction history
+
Manually labeled evaluation examples
```

Clearly label synthetic data in the research report.

Do not claim synthetic evaluation represents real-world employee
behavior.

------------------------------------------------------------------------

# 33. Database Strategy

## PostgreSQL

Use for:

-   Users
-   Employees
-   Profiles
-   Roles
-   Resources
-   Assessments
-   Progress
-   Evidence metadata
-   Recommendations
-   Feedback

## Neo4j

Use for:

-   Skill relationships
-   Prerequisites
-   Resource relationships
-   Mentor expertise
-   Role-skill relationships
-   Graph traversal

## pgvector

Use for:

-   Skill embeddings
-   Course embeddings
-   Project embeddings
-   JD embeddings
-   Semantic retrieval

## Redis

Use for:

-   Cache
-   Sessions where appropriate
-   Background queues

------------------------------------------------------------------------

# 34. Folder Structure

Maintain the PRD's modular structure:

``` text
skillpath-ai/
├── frontend/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── db/
│   ├── alembic/
│   └── tests/
├── ml/
│   ├── skill_extraction/
│   ├── embeddings/
│   └── evidence/
├── recommendation/
├── knowledge_graph/
├── optimization/
├── llm/
├── database/
├── datasets/
├── tests/
├── docs/
└── scripts/
```

Do not allow business logic to accumulate inside API route files.

------------------------------------------------------------------------

# 35. Documentation Strategy

Maintain:

``` text
docs/
├── architecture/
├── api/
├── research/
└── user_guides/
```

Create at least:

``` text
architecture.md
database.md
recommendation.md
skill-gap-model.md
knowledge-graph.md
optimization.md
evaluation.md
api.md
setup.md
```

Update documentation after every major phase.

------------------------------------------------------------------------

# 36. Git Strategy

Use meaningful commits.

Examples:

``` text
feat(auth): add JWT authentication
feat(profile): add employee profile CRUD
feat(skills): add skill taxonomy
feat(nlp): add resume skill extraction
feat(gap): implement weighted skill-gap model
feat(recommendation): add semantic ranking
feat(graph): add Neo4j prerequisite graph
feat(path): add topological learning paths
feat(opt): add OR-Tools optimizer
feat(assessment): add adaptive assessment updates
feat(llm): add grounded learning assistant
test(recommendation): add ranking evaluation
```

Avoid giant commits containing multiple unrelated features.

------------------------------------------------------------------------

# 37. Definition of Done for Every Feature

A feature is NOT complete when the code merely runs.

Every feature must have:

``` text
Implementation
+
Unit Tests
+
Integration Test where applicable
+
API validation
+
Error handling
+
Logging where useful
+
Documentation
+
README/update if setup changed
```

For ML components:

``` text
Implementation
+
Evaluation
+
Example inputs/outputs
+
Known limitations
```

For recommendation components:

``` text
Algorithm
+
Score breakdown
+
Explanation
+
Evaluation
```

------------------------------------------------------------------------

# 38. Recommended Implementation Order

The exact order should be:

``` text
1. Repository setup
2. Docker/PostgreSQL
3. FastAPI skeleton
4. React skeleton
5. Authentication
6. Employee profile
7. Skill taxonomy
8. Resume upload
9. Resume parser
10. Skill extraction
11. Skill normalization
12. Role/JD extraction
13. Basic gap engine
14. Course dataset
15. Content-based recommendation
16. Basic learning path
17. Neo4j graph
18. Evidence model
19. Confidence aggregation
20. Semantic recommendation
21. Hybrid recommendation
22. Project recommendation
23. Mentor recommendation
24. Prerequisite-aware path
25. OR-Tools optimization
26. Assessment engine
27. Adaptive re-optimization
28. Explainability
29. RAG assistant
30. GitHub integration
31. What-if simulation
32. Skill digital twin
33. Manager/HR analytics
34. Evaluation
35. Docker deployment
36. Documentation
```

------------------------------------------------------------------------

# 39. Do Not Over-Engineer Early

Do NOT start with:

-   Neo4j before basic data exists
-   OR-Tools before a simple path exists
-   LLM before deterministic extraction works
-   Collaborative filtering before interaction data exists
-   GitHub integration before the core skill model works
-   Microservices before the modular monolith is stable

Build the simplest correct version first.

Then replace individual components with more sophisticated
implementations.

------------------------------------------------------------------------

# 40. Milestone Checkpoints

## Milestone 1 --- Week 2

Working:

``` text
Auth
Profile
PostgreSQL
React dashboard
```

## Milestone 2 --- Week 4

Working:

``` text
Resume
→ Skills
→ Taxonomy
```

## Milestone 3 --- Week 6

Working:

``` text
Employee
→ Target Role
→ Skill Gaps
```

## Milestone 4 --- Week 8

Working:

``` text
Skill Gaps
→ Course Recommendations
```

## Milestone 5 --- Week 10

Working:

``` text
Skill Gaps
→ Knowledge Graph
→ Prerequisites
```

## Milestone 6 --- Week 12

Working:

``` text
Graph
→ Optimized Learning Path
```

## Milestone 7 --- Week 14

Working:

``` text
Courses
+
Projects
+
Mentors
```

## Milestone 8 --- Week 16

Working:

``` text
Assessment
→ Skill Update
→ Adaptive Path
```

## Milestone 9 --- Week 18

Working:

``` text
Explainability
+
RAG Assistant
```

## Milestone 10 --- Week 20

Working:

``` text
Complete system
+
Evaluation
+
Docker deployment
+
Research documentation
```

------------------------------------------------------------------------

# 41. Final Demonstration Scenario

The final demo should tell one coherent story.

Use a sample employee:

``` text
Role:
Software Engineer

Experience:
2 years

Skills:
Python 4
SQL 3.5
Git 4
ML 2

Target:
ML Engineer

Availability:
10 hours/week
```

Then demonstrate:

``` text
1. Upload resume
2. Extract skills
3. Show evidence
4. Select target role
5. Calculate gaps
6. Expand prerequisites
7. Recommend courses
8. Recommend projects
9. Recommend mentor
10. Generate optimized path
11. Explain every recommendation
12. Take assessment
13. Update skill
14. Re-optimize path
15. Ask AI assistant a question
16. Open digital skill twin
17. Compare another target role
```

This should be the final end-to-end product story.

------------------------------------------------------------------------

# 42. Final Research Story

The project should ultimately demonstrate this transformation:

``` text
Traditional Learning Platform

Employee
   ↓
Course List
```

versus:

``` text
SkillPath AI

Employee Evidence
       ↓
Evidence-Based Skill Profile
       ↓
Confidence-Aware Skill Gaps
       ↓
Knowledge Graph
       ↓
Prerequisite Reasoning
       ↓
Hybrid Recommendation
       ↓
Courses + Projects + Mentors
       ↓
Constraint-Optimized Path
       ↓
Assessment
       ↓
Updated Evidence
       ↓
Adaptive Re-optimization
```

The second system is the actual research/product contribution.

------------------------------------------------------------------------

# 43. Final Cursor Execution Rules

When this project is handed to Cursor:

### Rule 1

Read the complete PRD and this implementation plan before modifying
code.

### Rule 2

Do not implement multiple future phases simultaneously.

### Rule 3

At the beginning of every phase, state:

``` text
Current Phase
Objective
PRD requirements being implemented
Files to create/change
Dependencies
Tests required
Definition of Done
```

### Rule 4

Before coding, inspect the existing repository.

Never overwrite existing work without understanding it.

### Rule 5

After coding:

``` text
Run tests
Run lint
Run type checks
Run application
Verify endpoints
Verify UI
```

### Rule 6

Fix errors before moving to the next phase.

### Rule 7

At the end of every phase, create/update a short progress record:

``` text
Phase:
Completed:
Files changed:
Tests:
Known issues:
Next phase:
```

### Rule 8

Never invent requirements that conflict with the PRD.

### Rule 9

If a technology in the PRD is temporarily unavailable, create a clean
abstraction so it can be replaced later.

### Rule 10

Do not declare the project complete merely because the frontend renders.
The recommendation, skill-gap, graph, optimization, assessment, and
evaluation pipelines must actually work.

------------------------------------------------------------------------

# 44. Final Definition of Success

The project is complete when a new employee can enter the system and the
platform can reliably perform:

``` text
Profile Creation
        ↓
Resume/JD Understanding
        ↓
Skill Extraction
        ↓
Evidence Aggregation
        ↓
Skill Confidence
        ↓
Skill Gap
        ↓
Prerequisite Discovery
        ↓
Course Recommendation
        ↓
Project Recommendation
        ↓
Mentor Recommendation
        ↓
Optimized Learning Path
        ↓
Assessment
        ↓
Skill Verification
        ↓
Adaptive Re-optimization
        ↓
Explainable Result
```

and the research implementation can demonstrate, through controlled
experiments, whether the proposed hybrid/prerequisite-aware approach
improves over simpler recommendation baselines.

------------------------------------------------------------------------

# 45. Immediate Next Action

Start with **Phase 0 and Phase 1 only**.

Do not implement the recommendation engine, knowledge graph,
optimization, LLM assistant, GitHub integration, or advanced UI yet.

First produce a stable foundation.

Once Phase 1 passes its Definition of Done, move to Phase 2.

This prevents the project from becoming a large collection of partially
implemented features.
