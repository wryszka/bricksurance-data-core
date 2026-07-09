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
};

export const REPO = {
  title: 'Repository (open source)',
  url: 'https://github.com/wryszka/bricksurance-data-core',
  description: 'The full open-source project: model specs, pipelines, tools and this app.',
};

// Ordered list for the Documents panel.
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
];
