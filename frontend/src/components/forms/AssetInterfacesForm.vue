<template>
  <div>
    <div class="flex align-items-center mb-2">
      <span>{{ t('assets.strings.networkInterfacesSummary', { count: localInterfaces.length }) }}</span>
      <Button class="ml-2 p-button-text p-button-sm" :label="expanded ? t('common.actions.hide') : t('common.actions.show')" icon="pi pi-chevron-down" @click="expanded = !expanded" />
    </div>
    <transition name="fade">
      <div v-if="expanded">
        <DataTable :value="localInterfaces" responsiveLayout="scroll" class="p-datatable-sm mb-3">
          <Column field="name" :header="t('assets.interfaces.name')" />
          <Column field="type" :header="t('assets.interfaces.type')" />
          <Column field="ip_address" :header="t('assets.interfaces.ipAddress')" />
          <Column field="mac_address" :header="t('assets.interfaces.macAddress')" />
          <Column field="vlan" :header="t('assets.interfaces.vlan')" />
          <Column field="default_gateway" :header="t('assets.interfaces.gateway')" />
          <Column field="subnet_mask" :header="t('assets.interfaces.subnet')" />
          <Column field="protocols" :header="t('assets.interfaces.protocols')">
            <template #body="{ data }">
              <div v-if="data.protocols && data.protocols.length" class="protocol-chips">
                <span v-for="(protocol, idx) in data.protocols" :key="protocol + idx" class="protocol-chip">
                  {{ protocol }}
                </span>
              </div>
              <span v-else class="text-muted">-</span>
            </template>
          </Column>
          <Column field="other" :header="t('assets.interfaces.other')" />
          <Column v-if="editable" :header="t('common.strings.actions')" style="width:120px">
            <template #body="slotProps">
              <Button icon="pi pi-pencil" class="p-button-text p-button-sm mr-2" @click="editInterface(slotProps.index)" />
              <Button icon="pi pi-trash" class="p-button-text p-button-danger p-button-sm" @click="removeInterface(slotProps.index)" />
            </template>
          </Column>
        </DataTable>
      </div>
    </transition>
    <Button v-if="editable" :label="t('assets.interfaces.addInterface')" icon="pi pi-plus" class="p-button-sm mt-2" @click="addInterface" />
    <Button v-if="editable" :label="t('assets.interfaces.addMultiple')" icon="pi pi-plus" class="p-button-sm mt-2 ml-2" @click="showBulkDialog = true" />

    <Dialog v-model:visible="showDialog" :header="dialogIndex === null ? t('assets.interfaces.addInterface') : t('assets.interfaces.editInterface')" :modal="true" :closable="false" :style="{width: '500px'}">
      <form @submit.prevent="saveDialog">
        <div class="p-fluid">
          <div class="p-field">
            <label for="name">{{ t('assets.interfaces.name') }}*</label>
            <InputText id="name" v-model="dialogData.name" required />
          </div>
          <div class="p-field">
            <label for="type">{{ t('assets.interfaces.type') }}*</label>
            <Dropdown id="type" v-model="dialogData.type" :options="interfaceTypeOptions" optionLabel="label" optionValue="value" placeholder="Select type" required />
          </div>
          <div v-if="dialogData.type === 'other'" class="p-field">
            <label for="type_custom">{{ t('assets.interfaces.typeCustom') }}</label>
            <InputText id="type_custom" v-model="dialogData.type_custom" placeholder="Specify the type" />
          </div>
          <div class="p-field">
            <label for="ip_address">{{ t('assets.interfaces.ipAddress') }}</label>
            <InputText id="ip_address" v-model="dialogData.ip_address" @blur="validateIP" />
            <small v-if="ipError" class="p-error">{{ t('assets.interfaces.invalidIP') }}</small>
          </div>
          <div class="p-field">
            <label for="subnet_mask">{{ t('assets.interfaces.subnet') }}</label>
            <InputText id="subnet_mask" v-model="dialogData.subnet_mask" @blur="validateSubnet" />
            <small v-if="subnetError" class="p-error">{{ t('assets.interfaces.invalidSubnet') }}</small>
          </div>
          <div class="p-field">
            <label for="default_gateway">{{ t('assets.interfaces.gateway') }}</label>
            <InputText id="default_gateway" v-model="dialogData.default_gateway" @blur="validateGateway" />
            <small v-if="gatewayError" class="p-error">{{ t('assets.interfaces.invalidGateway') }}</small>
          </div>
          <div class="p-field">
            <label for="mac_address">{{ t('assets.interfaces.macAddress') }}</label>
            <InputText id="mac_address" v-model="dialogData.mac_address" @blur="validateMAC" />
            <small v-if="macError" class="p-error">{{ t('assets.interfaces.invalidMAC') }}</small>
          </div>
          <div class="p-field">
            <label for="vlan">{{ t('assets.interfaces.vlan') }}</label>
            <InputText id="vlan" v-model="dialogData.vlan" />
          </div>
          <div class="p-field">
            <label for="logical_port">{{ t('assets.interfaces.logicalPort') }}</label>
            <InputText id="logical_port" v-model="dialogData.logical_port" />
          </div>
          <div class="p-field">
            <label for="physical_plug_label">{{ t('assets.interfaces.plugLabel') }}</label>
            <InputText id="physical_plug_label" v-model="dialogData.physical_plug_label" />
          </div>
          <div class="p-field">
            <label for="other">{{ t('assets.interfaces.other') }}</label>
            <InputText id="other" v-model="dialogData.other" />
          </div>
          <div class="p-field">
            <label for="protocols">{{ t('assets.interfaces.protocols') }}</label>
            <MultiSelect
              id="protocols"
              v-model="dialogData.protocols"
              :options="protocolOptions"
              :filter="true"
              :placeholder="t('assets.interfaces.protocolPlaceholder')"
              display="chip"
              :maxSelectedLabels="3"
              class="w-full"
            />
            <div class="mt-2 flex align-items-center">
              <InputText id="new_protocol" v-model="newProtocol" :placeholder="t('assets.interfaces.addProtocol')" @keyup.enter="addProtocol" class="mr-2" style="width:200px" />
              <Button label="+" @click="addProtocol" size="small" />
            </div>
            <small class="text-gray-600">
              {{ t('assets.interfaces.protocolsNote') }}
            </small>
          </div>
          <div class="p-field">
            <label for="details">{{ t('assets.interfaces.details') }} (JSON)</label>
            <InputText id="details" v-model="detailsString" :placeholder="t('assets.interfaces.detailsPlaceholder')" />
            <small v-if="detailsError" class="p-error">{{ t('assets.interfaces.invalidDetails') }}</small>
          </div>
        </div>
        <div class="flex justify-content-end gap-2 mt-3">
          <Button :label="t('common.actions.save')" icon="pi pi-check" type="submit" class="p-button-sm" />
          <Button :label="t('common.actions.cancel')" icon="pi pi-times" type="button" class="p-button-secondary p-button-sm" @click="closeDialog" />
        </div>
      </form>
    </Dialog>

    <Dialog v-model:visible="showBulkDialog" :header="t('assets.interfaces.addMultiple')" :modal="true" :closable="false" :style="{width: '400px'}">
      <form @submit.prevent="bulkCreateInterfaces">
        <div class="p-fluid">
          <div class="p-field">
            <label for="bulk_count">{{ t('assets.interfaces.bulkCount') }}*</label>
            <InputText id="bulk_count" v-model.number="bulkCount" type="number" min="1" required />
          </div>
          <div class="p-field">
            <label for="bulk_prefix">{{ t('assets.interfaces.bulkPrefix') }}*</label>
            <InputText id="bulk_prefix" v-model="bulkPrefix" required />
          </div>
          <div class="p-field">
            <label for="bulk_type">{{ t('assets.interfaces.type') }}*</label>
            <Dropdown id="bulk_type" v-model="bulkType" :options="interfaceTypeOptions" optionLabel="label" optionValue="value" placeholder="Select type" required />
          </div>
          <div v-if="bulkType === 'other'" class="p-field">
            <label for="bulk_type_custom">{{ t('assets.interfaces.typeCustom') }}</label>
            <InputText id="bulk_type_custom" v-model="bulkTypeCustom" placeholder="Specify the type" />
          </div>
          <!-- Other optional parameters can be added here -->
        </div>
        <div class="flex justify-content-end gap-2 mt-3">
          <Button :label="t('common.actions.save')" icon="pi pi-check" type="submit" class="p-button-sm" />
          <Button :label="t('common.actions.cancel')" icon="pi pi-times" type="button" class="p-button-secondary p-button-sm" @click="showBulkDialog = false" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import Dropdown from 'primevue/dropdown';
import MultiSelect from 'primevue/multiselect';
import api from '@/api/api'

function isValidIP(ip) {
  if (!ip) return true;
  return /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(ip);
}
function isValidMAC(mac) {
  if (!mac) return true;
  return /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/.test(mac);
}

export default {
  name: 'AssetInterfacesForm',
  components: { DataTable, Column, Button, Dialog, InputText, Dropdown, MultiSelect },
  props: {
    interfaces: {
      type: Array,
      default: () => []
    },
    editable: {
      type: Boolean,
      default: false
    },
    assetId: {
      type: [String, Number],
      required: false
    },
    tenantId: {
      type: [String, Number],
      required: false
    }
  },
  emits: ['update:interfaces'],
  setup() {
    const { t } = useI18n();
    const interfaceTypeOptions = [
      { label: 'Ethernet', value: 'ethernet' },
      { label: 'Fibra', value: 'fiber' },
      { label: 'Seriale', value: 'serial' },
      { label: 'Wi-Fi', value: 'wifi' },
      { label: 'Altro', value: 'other' }
    ];
    
    // Load protocols from backend
    const loadProtocolOptions = async () => {
      try {
        const response = await api.getInterfaceProtocols();
        return response.data.protocols || [];
      } catch (error) {
        console.error('Error loading interface protocols:', error);
        // Fallback to default protocols
        return [
          'Modbus TCP',
          'Modbus RTU', 
          'EtherNet/IP',
          'DNP3',
          'BACNet',
          'OPC UA',
          'HTTP',
          'HTTPS',
          'FTP',
          'SFTP',
          'MQTT',
          'CoAP',
          'XMPP',
          'SNMP',
          'Syslog',
          'NTP',
          'DNS',
          'DHCP',
          'RADIUS',
          'LDAP',
          'Kerberos',
          'TLS',
          'SSL',
          'SSH',
          'Telnet',
          'Seriale',
          'Altro'
        ];
      }
    };
    
    return { t, interfaceTypeOptions, loadProtocolOptions };
  },
  data() {
    return {
      // Keep all interface fields, including technical fields
      localInterfaces: this.copyInterfaces(this.interfaces),
      showDialog: false,
      dialogIndex: null,
      dialogData: this.emptyInterface(),
      detailsString: '',
      detailsError: false,
      ipError: false,
      macError: false,
      subnetError: false,
      gatewayError: false,
      showBulkDialog: false,
      bulkCount: 1,
      bulkPrefix: 'eth',
      bulkType: '',
      bulkTypeCustom: '',
      expanded: false,
      newProtocol: '',
      protocolOptions: [], // Will be loaded dynamically
    }
  },
  watch: {
    interfaces: {
      handler(newVal) {
        this.localInterfaces = this.copyInterfaces(newVal);
      },
      deep: true
    }
  },
  async mounted() {
    // Load supported protocols
    this.protocolOptions = await this.loadProtocolOptions();
  },
  methods: {
    // Deep copy of interfaces, keeping all fields
    copyInterfaces(arr) {
      return arr.map(i => ({ ...i }));
    },
    emptyInterface() {
      return {
        name: '',
        type: '',
        vlan: '',
        logical_port: '',
        physical_plug_label: '',
        details: {},
        ip_address: '',
        subnet_mask: '',
        default_gateway: '',
        mac_address: '',
        other: '',
        protocols: []
        // Technical fields (id, asset_id, tenant_id, created_at) will be added by the backend for new interfaces
      };
    },
    addInterface() {
      this.dialogIndex = null;
      this.dialogData = this.emptyInterface();
      this.detailsString = '';
      this.detailsError = false;
      this.resetErrors();
      this.showDialog = true;
    },
    editInterface(idx) {
      this.dialogIndex = idx;
      // Copy all fields, including technical fields
      this.dialogData = { ...this.localInterfaces[idx] };
      this.detailsString = this.dialogData.details ? JSON.stringify(this.dialogData.details, null, 2) : '';
      this.detailsError = false;
      this.resetErrors();
      this.showDialog = true;
    },
    removeInterface(idx) {
      this.localInterfaces.splice(idx, 1);
      this.emitChange();
    },
    saveDialog() {
      if (!this.dialogData.name || !this.dialogData.type) return;
      if (this.dialogData.type === 'other' && !this.dialogData.type_custom) return;
      if (!isValidIP(this.dialogData.ip_address)) { this.ipError = true; return; }
      if (!isValidIP(this.dialogData.subnet_mask)) { this.subnetError = true; return; }
      if (!isValidIP(this.dialogData.default_gateway)) { this.gatewayError = true; return; }
      if (!isValidMAC(this.dialogData.mac_address)) { this.macError = true; return; }
      let details = {};
      if (this.detailsString.trim()) {
        try {
          details = JSON.parse(this.detailsString);
          this.detailsError = false;
        } catch (e) {
          this.detailsError = true;
          return;
        }
      }
      this.dialogData.details = details;
      // Normalizza il tipo: se è un tipo standard, capitalizza la prima lettera per consistenza
      let typeToSave = this.dialogData.type === 'other' ? this.dialogData.type_custom : this.dialogData.type;
      // Normalizza i tipi standard (ethernet -> Ethernet, wifi -> Wi-Fi, etc.)
      const typeMap = {
        'ethernet': 'Ethernet',
        'fiber': 'Fiber',
        'fibra': 'Fiber',
        'serial': 'Serial',
        'seriale': 'Serial',
        'wifi': 'Wi-Fi',
        'wi-fi': 'Wi-Fi'
      };
      if (typeMap[typeToSave?.toLowerCase()]) {
        typeToSave = typeMap[typeToSave.toLowerCase()];
      } else if (typeToSave && typeToSave !== 'other') {
        // Capitalizza la prima lettera per tipi custom
        typeToSave = typeToSave.charAt(0).toUpperCase() + typeToSave.slice(1).toLowerCase();
      }
      this.dialogData.type = typeToSave;
      // Add asset_id and tenant_id
      this.dialogData.asset_id = this.assetId;
      this.dialogData.tenant_id = this.tenantId;
      if (this.dialogIndex === null) {
        // New interface: no technical fields
        this.localInterfaces.push({ ...this.dialogData });
      } else {
        // Update: replace the object in the array (Vue 3)
        this.localInterfaces[this.dialogIndex] = { ...this.dialogData };
      }
      this.emitChange();
      this.closeDialog();
    },
    closeDialog() {
      this.showDialog = false;
      this.dialogData = this.emptyInterface();
      this.detailsString = '';
      this.detailsError = false;
      this.dialogIndex = null;
      this.resetErrors();
      this.newProtocol = '';
    },
    emitChange() {
      // Send always the complete structure of the interfaces, including technical fields
      this.$emit('update:interfaces', this.copyInterfaces(this.localInterfaces));
    },
    resetErrors() {
      this.ipError = false;
      this.macError = false;
      this.subnetError = false;
      this.gatewayError = false;
    },
    validateIP() { this.ipError = !isValidIP(this.dialogData.ip_address); },
    validateSubnet() { this.subnetError = !isValidIP(this.dialogData.subnet_mask); },
    validateGateway() { this.gatewayError = !isValidIP(this.dialogData.default_gateway); },
    validateMAC() { this.macError = !isValidMAC(this.dialogData.mac_address); },
    addProtocol() {
      if (this.newProtocol.trim() && !this.dialogData.protocols.includes(this.newProtocol.trim())) {
        this.dialogData.protocols.push(this.newProtocol.trim());
        this.newProtocol = '';
      }
    },
    async bulkCreateInterfaces() {
      if (!this.bulkCount || !this.bulkPrefix || !this.bulkType) return;
      if (this.bulkType === 'other' && !this.bulkTypeCustom) return;
      // Retrieve asset_id and tenant_id from props if available
      let asset_id = this.assetId || this.localInterfaces[0]?.asset_id || this.interfaces[0]?.asset_id;
      let tenant_id = this.tenantId || this.localInterfaces[0]?.tenant_id || this.interfaces[0]?.tenant_id;
      if (!asset_id || !tenant_id) {
        this.$toast?.add({ severity: 'error', summary: 'Error', detail: 'Unable to determine asset_id or tenant_id', life: 3000 });
        return;
      }
      let typeToUse = this.bulkType === 'other' ? this.bulkTypeCustom : this.bulkType;
      // Normalizza il tipo: capitalizza la prima lettera per consistenza
      const typeMap = {
        'ethernet': 'Ethernet',
        'fiber': 'Fiber',
        'fibra': 'Fiber',
        'serial': 'Serial',
        'seriale': 'Serial',
        'wifi': 'Wi-Fi',
        'wi-fi': 'Wi-Fi'
      };
      if (typeMap[typeToUse?.toLowerCase()]) {
        typeToUse = typeMap[typeToUse.toLowerCase()];
      } else if (typeToUse && typeToUse !== 'other') {
        // Capitalizza la prima lettera per tipi custom
        typeToUse = typeToUse.charAt(0).toUpperCase() + typeToUse.slice(1).toLowerCase();
      }
      const interfaces = [];
      for (let i = 1; i <= this.bulkCount; i++) {
        interfaces.push({
          name: `${this.bulkPrefix}${i}`,
          type: typeToUse,
          asset_id,
          tenant_id,
          vlan: null,
          logical_port: null,
          physical_plug_label: null,
          details: {},
          ip_address: null,
          subnet_mask: null,
          default_gateway: null,
          mac_address: null,
          other: null,
          protocols: []
        });
      }
      try {
        const res = await api.createAssetInterfacesBulk(interfaces);
        // Add the new interfaces to the local list
        this.localInterfaces.push(...res.data);
        this.emitChange();
        this.showBulkDialog = false;
        this.bulkCount = 1;
        this.bulkPrefix = 'eth';
        this.bulkType = '';
        this.bulkTypeCustom = '';
      } catch (e) {
        this.$toast?.add({ severity: 'error', summary: 'Error', detail: 'Massive creation failed', life: 3000 });
      }
    }
  }
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}

.protocol-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.protocol-chip {
  background-color: #e3f2fd;
  color: #1976d2;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid #bbdefb;
}

.text-muted {
  color: #6c757d;
  font-style: italic;
}
</style>
