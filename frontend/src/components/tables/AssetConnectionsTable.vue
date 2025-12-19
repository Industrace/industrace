<template>
  <div class="asset-connections-table">
    <div class="flex align-items-center mb-2">
      <span>{{ t('assets.connections.title') }}</span>
    </div>
    <table v-if="connections.length" class="conn-table">
      <thead>
        <tr>
          <th>{{ t('assets.connections.assetA') }}</th>
          <th>{{ t('assets.connections.interfaceA') }}</th>
          <th>{{ t('assets.connections.logicalPortA') }}</th>
          <th>{{ t('assets.connections.physicalPlugLabelA') }}</th>
          <th>{{ t('assets.connections.physicalPlugLabelB') }}</th>
          <th>{{ t('assets.connections.logicalPortB') }}</th>
          <th>{{ t('assets.connections.interfaceB') }}</th>
          <th>{{ t('assets.connections.assetB') }}</th>
          <th>{{ t('assetDependencies.hasDependency') }}</th>
          <th>{{ t('common.strings.actions') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, idx) in connections" :key="row.id || idx">
          <td>{{ row.assetA?.name || '-' }}</td>
          <td>{{ row.interfaceA?.name || '-' }}</td>
          <td>{{ row.interfaceA?.logical_port || '-' }}</td>
          <td>{{ row.interfaceA?.physical_plug_label || '-' }}</td>
          <td>{{ row.interfaceB?.physical_plug_label || '-' }}</td>
          <td>{{ row.interfaceB?.logical_port || '-' }}</td>
          <td>{{ row.interfaceB?.name || '-' }}</td>
          <td>{{ row.assetB?.name || '-' }}</td>
          <td>
            <Tag 
              v-if="row.dependency_status?.has_dependency"
              :value="t('assetDependencies.hasDependency')"
              severity="success"
              icon="pi pi-check"
            />
            <Tag 
              v-else-if="row.dependency_status?.status === 'missing'"
              :value="t('assetDependencies.missingDependency')"
              severity="danger"
              icon="pi pi-exclamation-triangle"
            />
            <Tag 
              v-else
              :value="t('assetDependencies.noDependency')"
              severity="warning"
              icon="pi pi-info-circle"
            />
          </td>
          <td>
            <Button 
              v-if="!row.dependency_status?.has_dependency"
              icon="pi pi-plus" 
              class="p-button-text p-button-sm mr-2" 
              @click="$emit('create-dependency', row)"
              v-tooltip.top="t('assetDependencies.createDependencyFromConnection')"
            />
            <Button icon="pi pi-pencil" class="p-button-text p-button-sm mr-2" @click="$emit('edit-connection', row)" />
            <Button icon="pi pi-trash" class="p-button-text p-button-danger p-button-sm" @click="$emit('delete-connection', row)" />
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="placeholder">
      <span>{{ t('assets.connections.noConnections') }}</span>
    </div>
  </div>
</template>

<script setup>
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Tooltip from 'primevue/tooltip'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
const props = defineProps({
  connections: { type: Array, default: () => [] }
})

defineEmits(['edit-connection', 'delete-connection', 'create-dependency'])
</script>

<style scoped>
.asset-connections-table {
  margin-bottom: 2em;
}
.conn-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}
.conn-table th, .conn-table td {
  border: 1px solid #e5e7eb;
  padding: 0.5em 0.75em;
  text-align: left;
}
.conn-table th {
  background: #f3f4f6;
}
.placeholder {
  text-align: center;
  color: #888;
  padding: 2em 0;
}
</style> 