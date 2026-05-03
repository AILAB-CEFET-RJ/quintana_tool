import { Table } from 'antd';
import { PaginationProps } from 'antd/lib/pagination';
import React, { useState } from 'react';

interface CustomTableProps {
    dataSource: any[];
    columns: any[];
    pagination?: PaginationProps | false;
    onChange?: (pagination: PaginationProps) => void;
}

const CustomTable: React.FC<CustomTableProps> = ({ dataSource, columns, pagination: controlledPagination, onChange }) => {
    const [pagination, setPagination] = useState<PaginationProps>({
        current: 1,
        pageSize: 10, 
    });

    const handleTableChange = (pagination: PaginationProps) => {
        if (!controlledPagination) {
            setPagination(pagination);
        }
        onChange?.(pagination);
    };

    return (
        <Table
            dataSource={dataSource}
            columns={columns}
            pagination={controlledPagination === undefined ? pagination : controlledPagination}
            onChange={handleTableChange}
        />
    );
};

export default CustomTable;
