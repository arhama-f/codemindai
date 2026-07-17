export interface FileTreeFile {
  id: string;
  path: string;
}

export interface TreeNode {
  name: string;
  fullPath: string;
  file?: FileTreeFile;
  children: Map<string, TreeNode>;
}

export function buildTree(files: FileTreeFile[]): TreeNode {
  const root: TreeNode = { name: "", fullPath: "", children: new Map() };

  for (const file of files) {
    const parts = file.path.split("/");
    let node = root;
    let accumulated = "";

    parts.forEach((part, index) => {
      accumulated = accumulated ? `${accumulated}/${part}` : part;
      const isLeaf = index === parts.length - 1;

      if (!node.children.has(part)) {
        node.children.set(part, { name: part, fullPath: accumulated, children: new Map() });
      }
      node = node.children.get(part)!;
      if (isLeaf) node.file = file;
    });
  }

  return root;
}

export function sortedEntries(node: TreeNode): TreeNode[] {
  return Array.from(node.children.values()).sort((a, b) => {
    const aIsDirectory = a.children.size > 0;
    const bIsDirectory = b.children.size > 0;
    if (aIsDirectory !== bIsDirectory) return aIsDirectory ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
}
