import { Card, Col, Row } from 'antd';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const demo = [
  { name: 'Jan', value: 120000 },
  { name: 'Feb', value: 160000 },
];

export default function Dashboard() {
  return (
    <div>
      <h1>WoodFlow Dashboard</h1>
      <Row gutter={16}>
        <Col span={6}><Card title="Выручка">1 250 000 ₽</Card></Col>
        <Col span={6}><Card title="Машины">14</Card></Col>
        <Col span={6}><Card title="Объем">312.5 м³</Card></Col>
        <Col span={6}><Card title="Пакеты на складе">98</Card></Col>
      </Row>
      <Card style={{ marginTop: 16 }} title="Выручка по месяцам">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={demo}><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="value" fill="#0F3D2E" /></BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
