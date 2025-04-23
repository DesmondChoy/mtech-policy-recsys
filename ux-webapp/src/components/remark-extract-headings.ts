// ux-webapp/src/components/remark-extract-headings.ts
import { Plugin } from 'unified';
import { visit } from 'unist-util-visit';
import type { Root } from 'mdast';

export interface HeadingData {
  depth: number;   // 1‑6
  value: string;   // raw text
  id: string;      // slug (kebab‑case)
}

interface Options {
  onHeadingsExtracted?: (headings: HeadingData[]) => void;
}

export const remarkExtractHeadings: Plugin<[Options?], Root> = (opts = {}) => {
  return (tree) => {
    const headings: HeadingData[] = [];

    visit(tree, 'heading', (node: any) => {
      const text = node.children
        .filter((c: any) => c.type === 'text')
        .map((c: any) => c.value)
        .join(' ');

      const id = text
        .toLowerCase()
        .trim()
        .replace(/[^\w]+/g, '-')
        .replace(/^-|-$/g, '');

      headings.push({ depth: node.depth, value: text, id });
    });

    if (typeof opts.onHeadingsExtracted === 'function') {
      opts.onHeadingsExtracted(headings);
    }
  };
};

export default remarkExtractHeadings;
