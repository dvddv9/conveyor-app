import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'category',
      label: 'Documentation',
      items: [
        'getting-started',
        'architecture',
        'api-reference',
        'cli',
      ],
    },
    {
      type: 'category',
      label: 'Case Studies',
      items: [
        'case-studies',
        'case-studies/curl-cookie-c',
      ],
    },
    {
      type: 'category',
      label: 'Legal',
      items: ['legal/terms', 'legal/privacy', 'legal/dpa', 'legal/sla'],
    },
  ],
};

export default sidebars;
