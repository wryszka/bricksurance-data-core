import { useEffect, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  Edge,
  Node,
  Position,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
} from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';
import { LineageNode, LineageResponse } from '../api';
import { href } from '../useHashRoute';

// Muted, palette-derived colours for the 16 domains. Reference nodes / code sets
// fall back to muted grey.
const DOMAIN_COLORS: Record<string, string> = {
  party: '#3f6f86',
  policy: '#12566e',
  coverage: '#2f7d8f',
  premium: '#c57a1f',
  claim: '#9c5a2a',
  reinsurance: '#5a6f8a',
  finance: '#4a7a5f',
  reserving: '#6a5a8a',
  actuarial: '#7a5a6a',
  regulatory: '#8a6a3a',
  distribution: '#3a7a7a',
  reference: '#8a94a0',
  product: '#5f8a4a',
  asset: '#4a6a8a',
  risk: '#8a4a4a',
  exposure: '#6a7a3a',
};

function colorFor(node: LineageNode): string {
  if (node.kind === 'code_set') return '#8a94a0';
  return DOMAIN_COLORS[node.domain] || '#5f7480';
}

const NODE_W = 190;
const NODE_H = 62;

function layout(nodes: Node[], edges: Edge[]): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'LR', nodesep: 26, ranksep: 90, marginx: 16, marginy: 16 });
  nodes.forEach((n) => g.setNode(n.id, { width: NODE_W, height: NODE_H }));
  edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);
  return nodes.map((n) => {
    const p = g.node(n.id);
    return {
      ...n,
      position: { x: p.x - NODE_W / 2, y: p.y - NODE_H / 2 },
      targetPosition: Position.Left,
      sourcePosition: Position.Right,
    };
  });
}

function buildNode(ln: LineageNode, center: string): Node {
  const isCenter = ln.id === center;
  const color = colorFor(ln);
  const certified = ln.certification === 'certified';
  return {
    id: ln.id,
    data: {
      label: (
        <div className="lg-node-inner" title={`${ln.label} (${ln.name})`}>
          {certified && <span className="lg-cert-dot" title="certified" />}
          <div className="lg-node-label">{ln.label}</div>
          <div className="lg-node-sub">{ln.name}</div>
        </div>
      ),
    },
    position: { x: 0, y: 0 },
    style: {
      width: NODE_W,
      minHeight: NODE_H,
      padding: 0,
      borderRadius: 9,
      border: isCenter ? `2px solid ${color}` : `1px solid ${color}55`,
      background: '#fff',
      borderLeft: `6px solid ${color}`,
      boxShadow: isCenter ? '0 4px 14px rgba(13,43,58,0.18)' : 'none',
      fontSize: 12,
    },
  };
}

interface Props {
  data: LineageResponse;
  height?: number;
  onNodeClick?: (node: LineageNode) => void;
  onExpand?: (node: LineageNode) => void;
  interactive?: boolean;
}

function detailHref(kind: string, name: string): string | null {
  if (kind === 'entity') return href(['entity', name]);
  if (kind === 'metric') return href(['metric', name]);
  if (kind === 'code_set') return href(['code_set', name]);
  if (kind === 'function') return href(['function', name]);
  return null;
}

function Inner({ data, height = 320, onNodeClick, onExpand, interactive = true }: Props) {
  const nodeById = useMemo(
    () => Object.fromEntries(data.nodes.map((n) => [n.id, n])),
    [data],
  );

  const initial = useMemo(() => {
    const rawNodes = data.nodes.map((n) => buildNode(n, data.center));
    const rawEdges: Edge[] = data.edges.map((e, i) => ({
      id: `e-${i}-${e.source}-${e.target}`,
      source: e.source,
      target: e.target,
      label: e.label,
      labelStyle: { fontSize: 10, fill: '#5f7480' },
      labelBgStyle: { fill: '#f4f6f7', fillOpacity: 0.9 },
      style: { stroke: '#b7c4cb', strokeWidth: 1.5 },
      animated: false,
    }));
    return { nodes: layout(rawNodes, rawEdges), edges: rawEdges };
  }, [data]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);

  useEffect(() => {
    setNodes(initial.nodes);
    setEdges(initial.edges);
  }, [initial, setNodes, setEdges]);

  const handleClick = (_: unknown, node: Node) => {
    const ln = nodeById[node.id];
    if (!ln) return;
    if (onNodeClick) onNodeClick(ln);
  };

  return (
    <div className="lineage-canvas" style={{ height }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleClick}
        onNodeDoubleClick={(_, node) => {
          const ln = nodeById[node.id];
          if (ln && onExpand) onExpand(ln);
        }}
        fitView
        fitViewOptions={{ padding: 0.18 }}
        nodesDraggable={interactive}
        nodesConnectable={false}
        elementsSelectable={interactive}
        panOnDrag={interactive}
        zoomOnScroll={interactive}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#dce4e8" gap={18} />
        {interactive && <Controls showInteractive={false} />}
      </ReactFlow>
    </div>
  );
}

export { detailHref };

export default function LineageGraph(props: Props) {
  return (
    <ReactFlowProvider>
      <Inner {...props} />
    </ReactFlowProvider>
  );
}
