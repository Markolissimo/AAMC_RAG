"""
Ground-truth Q&A pairs for evaluating the MCAT AI Tutor RAG system.

Each pair was manually crafted from the Princeton Review Fluid Dynamics and
ExamKrackers Fluids chapters. They serve as the evaluation dataset for:
  1. Retrieval quality (do relevant chunks surface for each question?)
  2. Generation quality (does the answer contain expected concepts?)
  3. MCAT question structure (does the generated MCQ have correct format?)

Structure per entry:
  - id            : unique identifier
  - question      : the student query sent to the system
  - expected_concepts : list of key terms/equations that MUST appear in the answer
  - expected_sections : list of structural sections that MUST appear (tutor format)
  - reference_answer  : gold-standard short answer for LLM-judge comparison
  - retrieval_keywords: terms expected to be present in retrieved chunks
  - topic         : broad topic tag
  - difficulty    : "easy" | "medium" | "hard" (MCAT difficulty)
  - source_hint   : which PDF(s) likely contain the answer
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QAPair:
    id: str
    question: str
    expected_concepts: list[str]
    expected_sections: list[str]
    reference_answer: str
    retrieval_keywords: list[str]
    topic: str
    difficulty: str = "medium"
    source_hint: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Expected structural sections (shared across all explanation Q&A)
# ---------------------------------------------------------------------------

TUTOR_SECTIONS = ["Core idea", "Simple picture", "MCAT concept", "Another analogy", "The Hook"]
MCAT_Q_SECTIONS = ["Question", "Answer Choices", "Correct Answer", "Explanation"]


# ===========================================================================
# EXPLANATION Q&A PAIRS
# ===========================================================================

EXPLANATION_QA_PAIRS: list[QAPair] = [

    # -----------------------------------------------------------------------
    # 1. Bernoulli's Principle — standard explanation
    # -----------------------------------------------------------------------
    QAPair(
        id="exp_001",
        question="Explain Bernoulli's principle.",
        expected_concepts=[
            "pressure",
            "velocity",
            "flow rate",
            "conservation of energy",
            "P + (1/2)*rho*v^2 + rho*g*h",
            "narrowing",
            "faster",
            "lower pressure",
        ],
        expected_sections=TUTOR_SECTIONS,
        reference_answer=(
            "Bernoulli's principle states that in a flowing fluid, an increase in "
            "velocity corresponds to a decrease in pressure (and vice versa), when "
            "height is constant. It is derived from conservation of energy: "
            "P + (1/2)*rho*v^2 + rho*g*h = constant. In a narrowing pipe, fluid "
            "speeds up (continuity equation: A1*v1 = A2*v2) and pressure drops. "
            "Common MCAT trap: students confuse higher speed with higher pressure."
        ),
        retrieval_keywords=["Bernoulli", "pressure", "velocity", "fluid", "energy"],
        topic="bernoullis_principle",
        difficulty="medium",
        source_hint=["Princeton", "ExamKrackers"],
    ),

    # -----------------------------------------------------------------------
    # 2. Bernoulli — simpler explanation
    # -----------------------------------------------------------------------
    QAPair(
        id="exp_002",
        question="Explain Bernoulli's principle in simpler terms.",
        expected_concepts=[
            "faster fluid",
            "lower pressure",
            "analogy",
        ],
        expected_sections=TUTOR_SECTIONS,
        reference_answer=(
            "When fluid moves faster, it pushes sideways less hard — so it has lower "
            "pressure. Think of air blowing between two pieces of paper: the fast "
            "moving air between them has lower pressure and the papers get sucked "
            "together. Fast flow = low pressure. Slow flow = high pressure."
        ),
        retrieval_keywords=["Bernoulli", "pressure", "velocity"],
        topic="bernoullis_principle",
        difficulty="easy",
        source_hint=["Princeton", "ExamKrackers"],
    ),

    # -----------------------------------------------------------------------
    # 3. Continuity Equation
    # -----------------------------------------------------------------------
    QAPair(
        id="exp_003",
        question="Explain the continuity equation and why fluid moves faster in a narrow pipe.",
        expected_concepts=[
            "A1*v1 = A2*v2",
            "cross-sectional area",
            "flow rate",
            "incompressible",
            "conservation of mass",
            "narrower pipe",
            "faster",
        ],
        expected_sections=TUTOR_SECTIONS,
        reference_answer=(
            "The continuity equation A1*v1 = A2*v2 states that flow rate Q = A*v is "
            "constant for an incompressible fluid. If the pipe narrows (smaller A), "
            "velocity v must increase to maintain the same flow rate. This is "
            "conservation of mass: the same amount of fluid per second must pass "
            "through a smaller opening, so it speeds up. MCAT trap: confusing flow "
            "rate Q (constant) with velocity v (changes with area)."
        ),
        retrieval_keywords=["continuity", "cross-sectional area", "flow rate", "velocity"],
        topic="continuity_equation",
        difficulty="medium",
        source_hint=["Princeton", "ExamKrackers"],
    ),

    # -----------------------------------------------------------------------
    # 4. Archimedes' Principle / Buoyancy
    # -----------------------------------------------------------------------
    QAPair(
        id="exp_004",
        question="Explain why objects float — Archimedes' principle.",
        expected_concepts=[
            "buoyant force",
            "displaced fluid",
            "density",
            "F_b = rho_fluid * V_displaced * g",
            "weight of displaced fluid",
            "float",
            "sink",
        ],
        expected_sections=TUTOR_SECTIONS,
        reference_answer=(
            "Archimedes' principle: the buoyant force on an object equals the weight "
            "of the fluid it displaces: F_b = rho_fluid * V_displaced * g. "
            "An object floats when F_b >= its weight (mg). This happens when "
            "rho_object <= rho_fluid. The object sinks until the volume submerged "
            "displaces enough fluid to equal its weight. MCAT trap: buoyancy depends "
            "on the FLUID's density, not the object's total mass."
        ),
        retrieval_keywords=["buoyancy", "Archimedes", "displaced", "density", "float"],
        topic="archimedes_principle",
        difficulty="medium",
        source_hint=["Princeton", "ExamKrackers"],
    ),

    # -----------------------------------------------------------------------
    # 5. Pascal's Principle
    # -----------------------------------------------------------------------
    QAPair(
        id="exp_005",
        question="Explain Pascal's principle and how hydraulic systems work.",
        expected_concepts=[
            "pressure",
            "transmitted equally",
            "F1/A1 = F2/A2",
            "hydraulic",
            "mechanical advantage",
            "incompressible fluid",
        ],
        expected_sections=TUTOR_SECTIONS,
        reference_answer=(
            "Pascal's principle: pressure applied to an enclosed fluid is transmitted "
            "equally in all directions. In a hydraulic system: F1/A1 = F2/A2 = P. "
            "A small force on a small piston creates the same pressure as a large "
            "force on a large piston. Mechanical advantage: F2 = F1 * (A2/A1). "
            "MCAT trap: the larger piston moves a shorter distance — energy is "
            "conserved, you can't get something for nothing."
        ),
        retrieval_keywords=["Pascal", "pressure", "hydraulic", "piston", "force"],
        topic="pascals_principle",
        difficulty="medium",
        source_hint=["Princeton", "ExamKrackers"],
    ),

    # -----------------------------------------------------------------------
    # 6. Hydrostatic Pressure
    # -----------------------------------------------------------------------
    QAPair(
        id="exp_006",
        question="Explain hydrostatic pressure and how pressure changes with depth.",
        expected_concepts=[
            "P = rho*g*h",
            "depth",
            "density",
            "gravity",
            "gauge pressure",
            "absolute pressure",
            "P_abs = P_atm + rho*g*h",
        ],
        expected_sections=TUTOR_SECTIONS,
        reference_answer=(
            "Hydrostatic pressure P = rho*g*h, where rho is fluid density, g is "
            "gravity, h is depth. Pressure increases linearly with depth because more "
            "fluid weight is above. Gauge pressure = pressure above atmospheric. "
            "Absolute pressure = atmospheric + gauge = P_atm + rho*g*h. "
            "MCAT trap: pressure depends only on depth and fluid density, NOT on "
            "the shape of the container or the total volume of fluid."
        ),
        retrieval_keywords=["hydrostatic", "pressure", "depth", "rho*g*h", "gauge"],
        topic="hydrostatic_pressure",
        difficulty="easy",
        source_hint=["Princeton", "ExamKrackers"],
    ),

    # -----------------------------------------------------------------------
    # 7. Poiseuille's Law
    # -----------------------------------------------------------------------
    QAPair(
        id="exp_007",
        question="Explain Poiseuille's law and its MCAT implications for blood flow.",
        expected_concepts=[
            "Q = (pi * r^4 * Delta_P) / (8 * eta * L)",
            "radius",
            "viscosity",
            "fourth power",
            "resistance",
            "R = 8*eta*L / (pi*r^4)",
            "blood vessels",
        ],
        expected_sections=TUTOR_SECTIONS,
        reference_answer=(
            "Poiseuille's law: Q = (pi * r^4 * Delta_P) / (8 * eta * L). "
            "Flow is proportional to r^4 — the fourth power of radius. "
            "Halving the radius reduces flow to 1/16th. Vascular resistance "
            "R = 8*eta*L / (pi*r^4). On the MCAT, arterial plaque reduces radius, "
            "dramatically reducing blood flow. MCAT trap: confusing r^2 (area) with "
            "r^4 (Poiseuille). The r^4 dependence is the most tested fact here."
        ),
        retrieval_keywords=["Poiseuille", "radius", "viscosity", "flow rate", "r^4"],
        topic="poiseuilles_law",
        difficulty="hard",
        source_hint=["Princeton", "ExamKrackers"],
    ),

    # -----------------------------------------------------------------------
    # 8. Laminar vs Turbulent Flow
    # -----------------------------------------------------------------------
    QAPair(
        id="exp_008",
        question="What is the difference between laminar and turbulent flow? What is the Reynolds number?",
        expected_concepts=[
            "laminar",
            "turbulent",
            "Reynolds number",
            "Re = rho*v*d / eta",
            "2000",
            "viscosity",
            "velocity",
            "streamline",
        ],
        expected_sections=TUTOR_SECTIONS,
        reference_answer=(
            "Laminar flow: smooth, parallel streamlines; occurs at low Reynolds number. "
            "Turbulent flow: chaotic, swirling; occurs at high Re. "
            "Reynolds number Re = rho*v*d / eta (density * velocity * diameter / viscosity). "
            "Re < 2000: laminar. Re > 4000: turbulent. 2000–4000: transitional. "
            "Poiseuille's law applies only to laminar flow. MCAT trap: high viscosity "
            "promotes laminar flow; high velocity promotes turbulence."
        ),
        retrieval_keywords=["laminar", "turbulent", "Reynolds", "viscosity", "flow"],
        topic="laminar_turbulent_flow",
        difficulty="medium",
        source_hint=["Princeton", "ExamKrackers"],
    ),

    # -----------------------------------------------------------------------
    # 9. Surface Tension
    # -----------------------------------------------------------------------
    QAPair(
        id="exp_009",
        question="Explain surface tension and capillary action.",
        expected_concepts=[
            "surface tension",
            "cohesion",
            "adhesion",
            "capillary action",
            "meniscus",
            "gamma",
        ],
        expected_sections=TUTOR_SECTIONS,
        reference_answer=(
            "Surface tension arises from cohesive forces between liquid molecules at "
            "the surface pulling inward, creating a 'skin.' Measured as force per unit "
            "length (N/m). Capillary action: liquid rises in a narrow tube when "
            "adhesion to the tube wall > cohesion between molecules (concave meniscus "
            "in water/glass). Falls when cohesion > adhesion (convex meniscus in "
            "mercury/glass). Height h = 2*gamma*cos(theta) / (rho*g*r). "
            "MCAT trap: capillary rise is HIGHER in narrower tubes (r in denominator)."
        ),
        retrieval_keywords=["surface tension", "capillary", "cohesion", "adhesion", "meniscus"],
        topic="surface_tension",
        difficulty="medium",
        source_hint=["Princeton", "ExamKrackers"],
    ),

    # -----------------------------------------------------------------------
    # 10. Bernoulli — analogy mode
    # -----------------------------------------------------------------------
    QAPair(
        id="exp_010",
        question="Give another analogy for Bernoulli's principle.",
        expected_concepts=[
            "analogy",
            "everyday",
            "speed",
            "pressure",
        ],
        expected_sections=["Another analogy"],  # relaxed — analogy mode doesn't need all sections
        reference_answer=(
            "A shower curtain blowing inward: fast-moving air from the shower head "
            "creates a low-pressure zone between you and the curtain. Higher pressure "
            "outside pushes the curtain in. Another classic: airplane wing — faster "
            "airflow over the curved top creates lower pressure → lift."
        ),
        retrieval_keywords=["Bernoulli", "pressure", "velocity"],
        topic="bernoullis_principle",
        difficulty="easy",
        source_hint=["Princeton", "ExamKrackers"],
    ),
]


# ===========================================================================
# MCAT QUESTION GENERATION EVALUATION PAIRS
# ===========================================================================

@dataclass
class MCATQAPair:
    """
    Spec for evaluating generated MCAT questions.
    We check structural correctness + concept coverage, not exact wording.
    """
    id: str
    topic: str
    question: str           # prompt to the system
    required_concepts: list[str]    # concepts that must appear in the question/explanation
    must_have_sections: list[str]   # structural sections the output must contain
    correct_answer_must_mention: list[str]  # keywords in the correct-answer rationale
    distractors_should_test: list[str]      # misconceptions the distractors probe
    difficulty: str = "medium"


MCAT_GENERATION_PAIRS: list[MCATQAPair] = [

    MCATQAPair(
        id="mcq_001",
        topic="buoyancy",
        question="Generate an MCAT question about buoyancy.",
        required_concepts=["buoyant force", "density", "displaced", "weight"],
        must_have_sections=MCAT_Q_SECTIONS,
        correct_answer_must_mention=["fluid density", "displaced volume"],
        distractors_should_test=[
            "object mass matters for float/sink",
            "denser objects always sink",
            "shape affects buoyancy",
        ],
        difficulty="medium",
    ),

    MCATQAPair(
        id="mcq_002",
        topic="Bernoulli's principle in a narrowing pipe",
        question="Generate an MCAT question about Bernoulli's principle.",
        required_concepts=["pressure", "velocity", "continuity", "Bernoulli"],
        must_have_sections=MCAT_Q_SECTIONS,
        correct_answer_must_mention=["velocity increases", "pressure decreases"],
        distractors_should_test=[
            "faster flow means higher pressure",
            "pressure constant throughout",
        ],
        difficulty="medium",
    ),

    MCATQAPair(
        id="mcq_003",
        topic="Poiseuille's law and blood vessel resistance",
        question="Generate an MCAT question about blood flow resistance using Poiseuille's law.",
        required_concepts=["radius", "r^4", "resistance", "flow rate"],
        must_have_sections=MCAT_Q_SECTIONS,
        correct_answer_must_mention=["r^4", "16-fold"],
        distractors_should_test=[
            "linear relationship with radius",
            "r^2 relationship",
        ],
        difficulty="hard",
    ),

    MCATQAPair(
        id="mcq_004",
        topic="Pascal's principle and hydraulic lift",
        question="Generate an MCAT question about Pascal's principle.",
        required_concepts=["pressure", "force", "area", "hydraulic"],
        must_have_sections=MCAT_Q_SECTIONS,
        correct_answer_must_mention=["equal pressure", "F/A"],
        distractors_should_test=[
            "output force equals input force",
            "larger piston moves same distance",
        ],
        difficulty="medium",
    ),

    MCATQAPair(
        id="mcq_005",
        topic="hydrostatic pressure at depth",
        question="Generate an MCAT question about hydrostatic pressure.",
        required_concepts=["rho*g*h", "depth", "density", "gauge pressure"],
        must_have_sections=MCAT_Q_SECTIONS,
        correct_answer_must_mention=["depth", "density"],
        distractors_should_test=[
            "pressure depends on container shape",
            "pressure depends on total volume",
        ],
        difficulty="easy",
    ),
]


# ===========================================================================
# Convenience accessors
# ===========================================================================

ALL_EXPLANATION_QUESTIONS = [p.question for p in EXPLANATION_QA_PAIRS]
ALL_MCQ_TOPICS            = [p.topic    for p in MCAT_GENERATION_PAIRS]

TOPIC_TO_EXPLANATION_QA: dict[str, QAPair] = {p.topic: p for p in EXPLANATION_QA_PAIRS}
ID_TO_EXPLANATION_QA:    dict[str, QAPair] = {p.id:    p for p in EXPLANATION_QA_PAIRS}
ID_TO_MCQ_PAIR:          dict[str, MCATQAPair] = {p.id: p for p in MCAT_GENERATION_PAIRS}
