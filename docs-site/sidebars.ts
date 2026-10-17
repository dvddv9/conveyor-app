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
        'case-studies',
      ],
    },
    {
      type: 'category',
      label: 'Legal',
      items: ['legal/terms', 'legal/privacy'],
    },
  ],
};

export default sidebars;
