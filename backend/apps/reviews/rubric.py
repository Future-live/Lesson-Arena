REVIEW_DIMENSIONS = [
    {
        "key": "objective_alignment",
        "label": "目标对齐度",
        "description": "教学目标是否明确、可测量，并与课程标准和学情匹配。",
        "weight": 0.14,
    },
    {
        "key": "content_structure",
        "label": "内容结构与逻辑",
        "description": "教学内容组织是否清晰，环节衔接是否自然，重点难点是否突出。",
        "weight": 0.13,
    },
    {
        "key": "activity_design",
        "label": "学习活动设计",
        "description": "课堂活动是否具体、可执行，能否促进学生真实参与与能力建构。",
        "weight": 0.14,
    },
    {
        "key": "question_guidance",
        "label": "问题引导与思维发展",
        "description": "问题链是否有层次，能否推动学生解释、迁移、推理和高阶思维发展。",
        "weight": 0.13,
    },
    {
        "key": "assessment_feedback",
        "label": "评价与反馈闭环",
        "description": "是否设计了形成性/终结性评价，并能支持及时反馈和改进。",
        "weight": 0.13,
    },
    {
        "key": "inclusion_engagement",
        "label": "学生参与与包容性",
        "description": "是否兼顾不同层次学生，体现差异化支持与课堂参与度设计。",
        "weight": 0.11,
    },
    {
        "key": "innovation_practicality",
        "label": "创新性与可落地性",
        "description": "是否有方法创新，同时仍具备真实课堂可执行性。",
        "weight": 0.11,
    },
    {
        "key": "language_norms",
        "label": "语言规范与文档质量",
        "description": "文本表达、格式、图文组织是否规范，便于实际教学使用。",
        "weight": 0.11,
    },
]

DIMENSION_MAP = {item["key"]: item for item in REVIEW_DIMENSIONS}
