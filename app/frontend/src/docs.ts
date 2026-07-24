// Central registry of project documents.
// Update URLs here — every "Read more" link and the Documents panel read from this.

export interface DocLink {
  key: string;
  title: string;
  url: string;
  description: string;
}

export const DOCS: Record<string, DocLink> = {
  overview: {
    key: 'overview',
    title: 'Overview',
    url: 'https://docs.google.com/document/d/1D2xxd7d0hVOuUHHacWYiuqFMF0p-IPyOYhRZyXQ5bQ0/edit',
    description: 'What Data Core is, the problem it solves, and how the pieces fit together.',
  },
  assets: {
    key: 'assets',
    title: 'Asset Inventory',
    url: 'https://docs.google.com/document/d/1VFVQhFZhNcavROUCpxveXn1tBADtnNlXSi-qEndWC_Q/edit',
    description: 'Every catalog, schema, table, view, share and job the demo deploys.',
  },
  tagging: {
    key: 'tagging',
    title: 'Tagging Strategy',
    url: 'https://docs.google.com/document/d/1nbN4MqmLljo1RRV6op51I2sZhXfotfkNGaIguiTy6Pw/edit',
    description: 'How classifications and ACORD / Lloyd’s standards tags are applied across the model.',
  },
  metrics: {
    key: 'metrics',
    title: 'Metrics Strategy',
    url: 'https://docs.google.com/document/d/1MWW-PNjESmRpbws0E_mx7QaNmQKrrrNQYO9JiG8mXI4/edit',
    description: 'How KPIs are defined once, as Unity Catalog metric views, for every consumer.',
  },
  cookbook: {
    key: 'cookbook',
    title: 'Demo Cookbook',
    url: 'https://docs.google.com/document/d/17wO71QHaGjoMkeFmM6xbINhGMybZZFiwbTNI2hDAows/edit',
    description: 'Step-by-step scripts for running each part of the demo end to end.',
  },
  gettingStarted: {
    key: 'gettingStarted',
    title: 'Getting Started',
    url: 'https://docs.google.com/document/d/1HoDqVqppgZqZGZpzyQV-xmFVM98gBIMPgWHyAvUR54Q/edit',
    description: 'Set up, deploy and run Data Core in your own Databricks workspace.',
  },
  adoption: {
    key: 'adoption',
    title: 'Adoption Path',
    url: 'https://docs.google.com/document/d/1t0yFTGIKJQLwzKCb5UEQ9WdpVq9lpL57twVRUg9ytr0/edit',
    description: 'How an organisation moves from a first table to a full shared ontology.',
  },
  evolution: {
    key: 'evolution',
    title: 'Model Evolution',
    url: 'https://docs.google.com/document/d/1O4jbJ-bhQVI65ibsEwFUM5oLFEYPPavP4hUj6Vn3xJE/edit',
    description: 'How the model changes safely over time, versioned in YAML.',
  },
  design: {
    key: 'design',
    title: 'Design & Architecture',
    url: 'https://docs.google.com/document/d/11kabV_nZDB2lwpqbsp3d3X7j1mjHzOagwRwB11WTnBU/edit',
    description: 'The end-to-end architecture and the design decisions behind it.',
  },
  genieCatalog: {
    key: 'genieCatalog',
    title: 'Genie Catalog',
    url: 'https://docs.google.com/document/d/1awgbB9aToP2ZwLKZ53aaQHN-SlxKfRIqbeCOp12IlIs/edit',
    description: 'What genies can we run? Five live spaces + the defined backlog.',
  },
  agentPlaybook: {
    key: 'agentPlaybook',
    title: 'Agent Playbook',
    url: 'https://docs.google.com/document/d/1M5__ezuSaVsBbSKrZFTq0DPRI2eviWrSHFClimqi1fU/edit',
    description: 'Can an agent do X? The governed action layer and the six shapes of any ask.',
  },
  topicCoverage: {
    key: 'topicCoverage',
    title: 'Topic Coverage Matrix',
    url: 'https://docs.google.com/document/d/1yEqIIpeByhbHhLpWdBBb-hZlnw7oG9_3gKpZuL5w8Gw/edit',
    description: '100 client topics stress-tested: 52 covered, 22 partial, 26 missing.',
  },
  // ---- Demo run-throughs (presenter-facing, per workbench / audience) ----
  leadersDemo: {
    key: 'leadersDemo',
    title: 'Demo — The Context Is the Moat (Databricks leaders)',
    url: 'https://docs.google.com/document/d/1iHVKfRhunS2UAjX0qhKQzbkxAn0FC8IB16FiDstYsUo/edit',
    description: 'The platform pitch: context is the moat, the model is a dial. Regulatory + lock-in + the wide Genie question.',
  },
  underwritingDemo: {
    key: 'underwritingDemo',
    title: 'Demo — Underwriting on the layer',
    url: 'https://docs.google.com/document/d/1j5GMQaRnC3Efn-OeKgQkzZutPB2TOI3XosrhSpLdUkc/edit',
    description: 'One agentic decision that grows up: submission → team → enterprise. With the pitch vs the Excel bolt-on.',
  },
  reservingDemo: {
    key: 'reservingDemo',
    title: 'Demo — Reserving on the layer',
    url: 'https://docs.google.com/document/d/1ZdNydA36ABBKbnqiw-76L42vCpObsbOmAi9D6swpm3M/edit',
    description: 'The living loss-development triangle, governed and reconciling. Plus the vs-Claude-for-Excel framing.',
  },
  atlasDemo: {
    key: 'atlasDemo',
    title: 'Demo — Insurance Ontology (App + Workspace)',
    url: 'https://docs.google.com/document/d/1wQoDuRBpgVd3FM1AIV7MwWpm5PNH1WJ2c9LQZ4l23og/edit',
    description: 'The search-first Atlas run: search a term, prove a number live, ask Genie. The front-door demo.',
  },
};

export const REPO = {
  title: 'Repository (open source)',
  url: 'https://github.com/wryszka/bricksurance-data-core',
  description: 'The full open-source project: model specs, pipelines, tools and this app.',
};

// Demo run-throughs — presenter-facing scripts, shown first in the panel.
export const DEMO_ORDER: DocLink[] = [
  DOCS.leadersDemo,
  DOCS.atlasDemo,
  DOCS.underwritingDemo,
  DOCS.reservingDemo,
];

// Reference docs — the full write-up behind Data Core.
export const DOC_ORDER: DocLink[] = [
  DOCS.overview,
  DOCS.gettingStarted,
  DOCS.design,
  DOCS.assets,
  DOCS.tagging,
  DOCS.metrics,
  DOCS.cookbook,
  DOCS.adoption,
  DOCS.evolution,
  DOCS.genieCatalog,
  DOCS.agentPlaybook,
  DOCS.topicCoverage,
];
