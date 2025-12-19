<template>
  <div class="conduit-form">
    <div class="p-fluid">
      <div class="field">
        <label>{{ t('common.fields.name') }} *</label>
        <InputText 
          v-model="formData.name" 
          :placeholder="t('isa62443.conduits.namePlaceholder')"
          required
        />
      </div>
      <div class="field">
        <label>{{ t('common.fields.description') }}</label>
        <Textarea 
          v-model="formData.description" 
          :rows="3"
          :placeholder="t('isa62443.conduits.descriptionPlaceholder')"
        />
      </div>
      <div class="grid">
        <div class="col-12 md:col-6">
          <div class="field">
            <label>{{ t('isa62443.conduits.fromZone') }} *</label>
            <Dropdown
              v-model="formData.from_zone_id"
              :options="zones"
              optionLabel="name"
              optionValue="id"
              :placeholder="t('isa62443.conduits.selectFromZone')"
              filter
              required
            />
          </div>
        </div>
        <div class="col-12 md:col-6">
          <div class="field">
            <label>{{ t('isa62443.conduits.toZone') }} *</label>
            <Dropdown
              v-model="formData.to_zone_id"
              :options="zones"
              optionLabel="name"
              optionValue="id"
              :placeholder="t('isa62443.conduits.selectToZone')"
              filter
              required
            />
          </div>
        </div>
      </div>
      <div class="field">
        <label>{{ t('isa62443.conduits.conduitType') }}</label>
        <Dropdown
          v-model="formData.conduit_type"
          :options="conduitTypeOptions"
          optionLabel="label"
          optionValue="value"
          :placeholder="t('isa62443.conduits.selectConduitType')"
        />
      </div>
      <div class="grid">
        <div class="col-12 md:col-6">
          <div class="field">
            <label>{{ t('isa62443.conduits.protocol') }}</label>
            <InputText 
              v-model="formData.protocol" 
              :placeholder="t('isa62443.conduits.protocolPlaceholder')"
            />
          </div>
        </div>
        <div class="col-12 md:col-6">
          <div class="field">
            <label>{{ t('isa62443.conduits.portRange') }}</label>
            <InputText 
              v-model="formData.port_range" 
              :placeholder="t('isa62443.conduits.portRangePlaceholder')"
            />
          </div>
        </div>
      </div>
      <div class="field">
        <label>{{ t('isa62443.conduits.allowedDirection') }}</label>
        <Dropdown
          v-model="formData.allowed_direction"
          :options="directionOptions"
          optionLabel="label"
          optionValue="value"
          :placeholder="t('isa62443.conduits.selectDirection')"
        />
      </div>
      <div class="field-checkbox">
        <Checkbox 
          v-model="formData.is_encrypted" 
          :binary="true"
          inputId="is_encrypted"
        />
        <label for="is_encrypted" class="ml-2">{{ t('isa62443.conduits.isEncrypted') }}</label>
      </div>
      <div v-if="formData.is_encrypted" class="field">
        <label>{{ t('isa62443.conduits.encryptionType') }}</label>
        <Dropdown
          v-model="formData.encryption_type"
          :options="encryptionTypeOptions"
          optionLabel="label"
          optionValue="value"
          :placeholder="t('isa62443.conduits.selectEncryptionType')"
        />
      </div>
      <div class="field-checkbox">
        <Checkbox 
          v-model="formData.authentication_required" 
          :binary="true"
          inputId="authentication_required"
        />
        <label for="authentication_required" class="ml-2">{{ t('isa62443.conduits.authenticationRequired') }}</label>
      </div>
      <div v-if="formData.authentication_required" class="field">
        <label>{{ t('isa62443.conduits.authenticationMethod') }}</label>
        <Dropdown
          v-model="formData.authentication_method"
          :options="authenticationMethodOptions"
          optionLabel="label"
          optionValue="value"
          :placeholder="t('isa62443.conduits.selectAuthenticationMethod')"
        />
      </div>
      <div class="field">
        <label>{{ t('isa62443.securityZones.securityLevelTarget') }} (SL-T)</label>
        <InputNumber 
          v-model="formData.security_level_target" 
          :min="1" 
          :max="4"
          :showButtons="true"
          class="w-full"
        />
      </div>
      <div class="field">
        <label>{{ t('isa62443.conduits.flowJustification') }}</label>
        <Textarea 
          v-model="formData.flow_justification" 
          :rows="3"
          :placeholder="t('isa62443.conduits.flowJustificationPlaceholder')"
        />
        <small class="text-muted">{{ t('isa62443.conduits.flowJustificationHelp') }}</small>
      </div>
      <div class="field">
        <label>{{ t('isa62443.conduits.ownership') }}</label>
        <InputText 
          v-model="formData.ownership" 
          :placeholder="t('isa62443.conduits.ownershipPlaceholder')"
        />
      </div>
      <div class="flex justify-content-end gap-2 mt-3">
        <Button 
          :label="t('common.actions.save')" 
          icon="pi pi-check" 
          @click="handleSubmit"
          :loading="saving"
        />
        <Button 
          :label="t('common.actions.cancel')" 
          icon="pi pi-times" 
          class="p-button-secondary" 
          @click="$emit('cancel')" 
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'

const props = defineProps({
  conduit: { type: Object, default: null },
  zones: { type: Array, required: true },
  defaultFromZone: { type: String, default: null }
})

const emit = defineEmits(['submit', 'cancel'])
const { t } = useI18n()

const formData = ref({
  name: '',
  description: '',
  from_zone_id: null,
  to_zone_id: null,
  conduit_type: null,
  protocol: '',
  port_range: '',
  allowed_direction: 'bidirectional',
  is_encrypted: false,
  encryption_type: null,
  authentication_required: true,
  authentication_method: null,
  security_level_target: null,
  flow_justification: '',
  ownership: ''
})

const saving = ref(false)

const conduitTypeOptions = [
  { label: t('isa62443.conduits.types.network'), value: 'network' },
  { label: t('isa62443.conduits.types.serial'), value: 'serial' },
  { label: t('isa62443.conduits.types.wireless'), value: 'wireless' },
  { label: t('isa62443.conduits.types.vpn'), value: 'vpn' },
  { label: t('isa62443.conduits.types.fieldbus'), value: 'fieldbus' },
  { label: t('isa62443.conduits.types.unidirectionalGateway'), value: 'unidirectional_gateway' },
  { label: t('isa62443.conduits.types.sharedService'), value: 'shared_service' },
  { label: t('isa62443.conduits.types.other'), value: 'other' }
]

const directionOptions = [
  { label: t('isa62443.conduits.directions.bidirectional'), value: 'bidirectional' },
  { label: t('isa62443.conduits.directions.unidirectional'), value: 'unidirectional' },
  { label: t('isa62443.conduits.directions.requestResponse'), value: 'request_response' }
]

const encryptionTypeOptions = [
  { label: 'TLS', value: 'tls' },
  { label: 'IPSec', value: 'ipsec' },
  { label: t('isa62443.conduits.encryptionTypes.proprietary'), value: 'proprietary' },
  { label: t('isa62443.conduits.encryptionTypes.other'), value: 'other' }
]

const authenticationMethodOptions = [
  { label: t('isa62443.conduits.authMethods.x509'), value: 'x509' },
  { label: t('isa62443.conduits.authMethods.usernamePassword'), value: 'username_password' },
  { label: t('isa62443.conduits.authMethods.psk'), value: 'psk' },
  { label: t('isa62443.conduits.authMethods.token'), value: 'token' },
  { label: t('isa62443.conduits.authMethods.kerberos'), value: 'kerberos' },
  { label: t('isa62443.conduits.authMethods.mtls'), value: 'mtls' },
  { label: t('isa62443.conduits.authMethods.other'), value: 'other' }
]

watch(() => props.conduit, (newConduit) => {
  if (newConduit) {
    formData.value = {
      name: newConduit.name || '',
      description: newConduit.description || '',
      from_zone_id: newConduit.from_zone_id || null,
      to_zone_id: newConduit.to_zone_id || null,
      conduit_type: newConduit.conduit_type || null,
      protocol: newConduit.protocol || '',
      port_range: newConduit.port_range || '',
      allowed_direction: newConduit.allowed_direction || 'bidirectional',
      is_encrypted: newConduit.is_encrypted || false,
      encryption_type: newConduit.encryption_type || null,
      authentication_required: newConduit.authentication_required ?? true,
      authentication_method: newConduit.authentication_method || null,
      security_level_target: newConduit.security_level_target || null,
      flow_justification: newConduit.flow_justification || '',
      ownership: newConduit.ownership || ''
    }
  } else {
    formData.value = {
      name: '',
      description: '',
      from_zone_id: props.defaultFromZone || null,
      to_zone_id: null,
      conduit_type: null,
      protocol: '',
      port_range: '',
      allowed_direction: 'bidirectional',
      is_encrypted: false,
      encryption_type: null,
      authentication_required: true,
      authentication_method: null,
      security_level_target: null,
      flow_justification: '',
      ownership: ''
    }
  }
}, { immediate: true })

function handleSubmit() {
  if (!formData.value.name || !formData.value.from_zone_id || !formData.value.to_zone_id) {
    return
  }
  emit('submit', { ...formData.value })
}
</script>

<style scoped>
.w-full {
  width: 100%;
}
</style>

