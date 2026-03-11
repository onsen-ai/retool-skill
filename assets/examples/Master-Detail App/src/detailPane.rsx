<SplitPaneFrame
  id="detailPane"
  _resizeHandleEnabled={true}
  enableFullBleed={true}
  hidden="{{ !customersTable.selectedRow.id }}"
  position="right"
  width="{{ { details: '350px', activity: '500px' }?.[detailTabs.value] ?? '350px' }}"
>
  <Container
    id="detailContainer"
    enableFullBleed={true}
    footerPadding="4px 12px"
    headerPadding="4px 12px"
    heightType="fixed"
    padding="12px"
    showBody={true}
    showHeader={true}
  >
    <Header>
      <Text
        id="detailTitle"
        marginType="normal"
        value="#### {{ customersTable.selectedRow.name }}"
        verticalAlign="center"
      />
      <Tabs
        id="detailTabs"
        itemMode="static"
        navigateContainer={true}
        targetContainerId="detailContainer"
        value="{{ self.values[0] }}"
      >
        <Option id="t1a2b" value="details" label="Details" />
        <Option id="t3c4d" value="activity" label="Activity" />
      </Tabs>
      <Button
        id="detailCloseBtn"
        horizontalAlign="right"
        iconBefore="bold/interface-delete-1"
        styleVariant="outline"
      >
        <Event
          id="ff11aa22"
          event="click"
          method="hide"
          params={{}}
          pluginId="detailPane"
          type="widget"
          waitMs="0"
          waitType="debounce"
        />
      </Button>
    </Header>
    <View id="detailsView" label="Details" viewKey="details">
      <Form
        id="DetailForm"
        disableSubmit="{{ updateCustomer.isFetching }}"
        initialData="{{ customersTable.selectedSourceRow }}"
        loading="{{ updateCustomer.isFetching }}"
        padding="12px"
        requireValidation={true}
        showBody={true}
        showFooter={true}
      >
        <Body>
          <TextInput
            id="detailName"
            formDataKey="name"
            label="Name"
            labelPosition="top"
            required={true}
          />
          <TextInput
            id="detailEmail"
            formDataKey="email"
            label="Email"
            labelPosition="top"
            required={true}
          />
          <Select
            id="detailStatus"
            formDataKey="status"
            itemMode="static"
            label="Status"
            labelPosition="top"
            showSelectionIndicator={true}
          >
            <Option id="s1a2b" value="active" label="Active" />
            <Option id="s3c4d" value="inactive" label="Inactive" />
            <Option id="s5e6f" value="pending" label="Pending" />
          </Select>
          <TextArea
            id="detailNotes"
            autoResize={true}
            formDataKey="notes"
            label="Notes"
            labelPosition="top"
            minLines={3}
          />
        </Body>
        <Footer>
          <Button
            id="detailSaveBtn"
            submit={true}
            submitTargetId="DetailForm"
            text="Save changes"
          />
        </Footer>
        <Event
          id="aa11bb22"
          event="submit"
          method="trigger"
          params={{ ordered: [] }}
          pluginId="updateCustomer"
          type="datasource"
          waitMs="0"
          waitType="debounce"
        />
      </Form>
    </View>
    <View id="activityView" label="Activity" viewKey="activity">
      <Text
        id="activityPlaceholder"
        value="Activity log for **{{ customersTable.selectedRow.name }}** will appear here.\n\nThis view demonstrates the tabbed detail pane pattern — each tab can show different content with different panel widths."
        verticalAlign="top"
      />
    </View>
  </Container>
</SplitPaneFrame>
