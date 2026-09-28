from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SkillPath AI"
    app_env: str = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+psycopg2://skillpath:skillpath@localhost:5435/skillpath"
    )

    secret_key: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12

    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    seed_on_startup: bool = True
    rate_limit_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("rate_limit_enabled", "RATE_LIMIT_ENABLED"),
    )
    rate_limit_requests: int = Field(
        default=120,
        ge=1,
        validation_alias=AliasChoices("rate_limit_requests", "RATE_LIMIT_REQUESTS"),
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        validation_alias=AliasChoices(
            "rate_limit_window_seconds", "RATE_LIMIT_WINDOW_SECONDS"
        ),
    )

    # Self-declaration is the lowest-reliability evidence source (PRD §33.4).
    self_declaration_reliability: float = Field(
        default=0.3,
        validation_alias=AliasChoices(
            "self_declaration_reliability", "SELF_DECLARATION_RELIABILITY"
        ),
    )
    resume_reliability: float = Field(
        default=0.6,
        validation_alias=AliasChoices("resume_reliability", "RESUME_RELIABILITY"),
    )
    resume_max_bytes: int = Field(default=5 * 1024 * 1024)
    resume_upload_dir: str = "var/uploads"
    jd_weight_required: float = Field(
        default=1.0,
        ge=0,
        le=1,
        validation_alias=AliasChoices("jd_weight_required", "JD_WEIGHT_REQUIRED"),
    )
    jd_weight_preferred: float = Field(
        default=0.6,
        ge=0,
        le=1,
        validation_alias=AliasChoices("jd_weight_preferred", "JD_WEIGHT_PREFERRED"),
    )
    jd_weight_mentioned: float = Field(
        default=0.4,
        ge=0,
        le=1,
        validation_alias=AliasChoices("jd_weight_mentioned", "JD_WEIGHT_MENTIONED"),
    )
    jd_max_bytes: int = Field(default=5 * 1024 * 1024)
    jd_upload_dir: str = "var/uploads/job_descriptions"
    github_reliability: float = Field(default=0.7, ge=0, le=1)
    course_reliability: float = Field(default=0.7, ge=0, le=1)
    assessment_reliability: float = Field(default=0.85, ge=0, le=1)
    assessment_pass_score: float = Field(default=0.7, ge=0, le=1)
    assessment_weak_score: float = Field(
        default=0.55,
        ge=0,
        le=1,
        validation_alias=AliasChoices("assessment_weak_score", "ASSESSMENT_WEAK_SCORE"),
    )
    assessment_strong_score: float = Field(
        default=0.90,
        ge=0,
        le=1,
        validation_alias=AliasChoices(
            "assessment_strong_score", "ASSESSMENT_STRONG_SCORE"
        ),
    )
    project_reliability: float = Field(default=0.75, ge=0, le=1)
    cert_reliability: float = Field(default=0.8, ge=0, le=1)
    work_reliability: float = Field(default=0.55, ge=0, le=1)
    evidence_conflict_variance: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices(
            "evidence_conflict_variance", "EVIDENCE_CONFLICT_VARIANCE"
        ),
    )
    evidence_confidence_high: float = Field(default=0.7, ge=0, le=1)
    evidence_confidence_medium: float = Field(default=0.4, ge=0, le=1)
    gap_weight_importance: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("gap_weight_importance", "GAP_WEIGHT_IMPORTANCE"),
    )
    gap_weight_confidence: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("gap_weight_confidence", "GAP_WEIGHT_CONFIDENCE"),
    )
    gap_weight_criticality: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices(
            "gap_weight_criticality", "GAP_WEIGHT_CRITICALITY"
        ),
    )
    gap_weight_evidence: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("gap_weight_evidence", "GAP_WEIGHT_EVIDENCE"),
    )
    gap_critical_threshold: float = Field(default=2.0, ge=0)
    gap_high_threshold: float = Field(default=1.0, ge=0)
    gap_medium_threshold: float = Field(default=0.5, ge=0)
    rec_top_gap_count: int = Field(default=5, ge=1, le=20)
    rec_result_limit: int = Field(default=10, ge=1, le=50)
    rec_semantic_backend: str = Field(
        default="hashing",
        validation_alias=AliasChoices("rec_semantic_backend", "REC_SEMANTIC_BACKEND"),
    )
    rec_semantic_model: str = Field(
        default="all-MiniLM-L6-v2",
        validation_alias=AliasChoices("rec_semantic_model", "REC_SEMANTIC_MODEL"),
    )
    rec_w_semantic: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_w_semantic", "REC_W_SEMANTIC"),
    )
    rec_w_gap: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_w_gap", "REC_W_GAP"),
    )
    rec_w_prerequisite: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_w_prerequisite", "REC_W_PREREQUISITE"),
    )
    rec_w_difficulty: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_w_difficulty", "REC_W_DIFFICULTY"),
    )
    rec_w_preference: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_w_preference", "REC_W_PREFERENCE"),
    )
    rec_w_collaborative: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_w_collaborative", "REC_W_COLLABORATIVE"),
    )
    rec_w_kg: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_w_kg", "REC_W_KG"),
    )
    rec_pair_limit: int = Field(default=5, ge=1, le=20)
    rec_p_skills: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_p_skills", "REC_P_SKILLS"),
    )
    rec_p_priority: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_p_priority", "REC_P_PRIORITY"),
    )
    rec_p_difficulty: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_p_difficulty", "REC_P_DIFFICULTY"),
    )
    rec_p_proficiency: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_p_proficiency", "REC_P_PROFICIENCY"),
    )
    rec_p_duration: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_p_duration", "REC_P_DURATION"),
    )
    rec_p_technologies: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_p_technologies", "REC_P_TECHNOLOGIES"),
    )
    rec_p_role: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_p_role", "REC_P_ROLE"),
    )
    rec_mentor_limit: int = Field(default=5, ge=1, le=20)
    rec_m_skill: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_m_skill", "REC_M_SKILL"),
    )
    rec_m_domain: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_m_domain", "REC_M_DOMAIN"),
    )
    rec_m_experience: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_m_experience", "REC_M_EXPERIENCE"),
    )
    rec_m_availability: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_m_availability", "REC_M_AVAILABILITY"),
    )
    rec_m_goals: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_m_goals", "REC_M_GOALS"),
    )
    rec_m_workload: float = Field(
        default=1.0,
        ge=0,
        validation_alias=AliasChoices("rec_m_workload", "REC_M_WORKLOAD"),
    )
    rec_path_foundation_level: float = Field(
        default=3.0,
        ge=0,
        le=5,
        validation_alias=AliasChoices(
            "rec_path_foundation_level", "REC_PATH_FOUNDATION_LEVEL"
        ),
    )
    rec_path_deadline_weeks: int = Field(
        default=12,
        ge=1,
        le=52,
        validation_alias=AliasChoices(
            "rec_path_deadline_weeks", "REC_PATH_DEADLINE_WEEKS"
        ),
    )
    neo4j_uri: str = Field(
        default="bolt://localhost:7688",
        validation_alias=AliasChoices("neo4j_uri", "NEO4J_URI"),
    )
    neo4j_user: str = Field(
        default="neo4j",
        validation_alias=AliasChoices("neo4j_user", "NEO4J_USER"),
    )
    neo4j_password: str = Field(
        default="skillpath",
        validation_alias=AliasChoices("neo4j_password", "NEO4J_PASSWORD"),
    )
    neo4j_sync_on_startup: bool = Field(
        default=True,
        validation_alias=AliasChoices("neo4j_sync_on_startup", "NEO4J_SYNC_ON_STARTUP"),
    )
    llm_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("llm_enabled", "LLM_ENABLED"),
    )
    llm_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("llm_api_key", "LLM_API_KEY", "NVIDIA_API_KEY"),
    )
    llm_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        validation_alias=AliasChoices("llm_base_url", "LLM_BASE_URL"),
    )
    llm_model: str = Field(
        default="openai/gpt-oss-20b",
        validation_alias=AliasChoices("llm_model", "LLM_MODEL"),
    )
    llm_timeout_seconds: float = Field(
        default=90.0,
        ge=5,
        le=90,
        validation_alias=AliasChoices("llm_timeout_seconds", "LLM_TIMEOUT_SECONDS"),
    )
    assistant_top_k: int = Field(default=8, ge=3, le=20)

    @field_validator("bcrypt_rounds")
    @classmethod
    def validate_bcrypt_rounds(cls, value: int) -> int:
        if value < 10:
            raise ValueError("bcrypt_rounds must be at least 10")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]

    def hybrid_weights(self) -> dict[str, float]:
        return {
            "semantic": self.rec_w_semantic,
            "gap": self.rec_w_gap,
            "prerequisite": self.rec_w_prerequisite,
            "difficulty": self.rec_w_difficulty,
            "preference": self.rec_w_preference,
            "collaborative": self.rec_w_collaborative,
            "kg": self.rec_w_kg,
        }

    def practice_weights(self) -> dict[str, float]:
        return {
            "skills_addressed": self.rec_p_skills,
            "gap_priority": self.rec_p_priority,
            "difficulty": self.rec_p_difficulty,
            "proficiency": self.rec_p_proficiency,
            "duration": self.rec_p_duration,
            "technologies": self.rec_p_technologies,
            "role": self.rec_p_role,
        }

    def mentor_weights(self) -> dict[str, float]:
        return {
            "skill_overlap": self.rec_m_skill,
            "domain_overlap": self.rec_m_domain,
            "experience": self.rec_m_experience,
            "availability": self.rec_m_availability,
            "learning_goals": self.rec_m_goals,
            "workload": self.rec_m_workload,
        }


settings = Settings()
