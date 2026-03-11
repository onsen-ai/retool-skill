<SplitPaneFrame
  id="detailPane"
  _resizeHandleEnabled={true}
  enableFullBleed={true}
  hidden="{{ !membersTable.selectedRow.id }}"
  position="right"
  width="{{ { details: '400px', activity: '550px' }?.[detailTabs.value] ?? '400px' }}"
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
        value="#### {{ membersTable.selectedRow.name }}"
        verticalAlign="center"
      />
      <Tabs
        id="detailTabs"
        itemMode="static"
        navigateContainer={true}
        targetContainerId="detailContainer"
        value="{{ self.values[0] }}"
      >
        <Option id="t1a1a" value="details" label="Details" />
        <Option id="t2b2b" value="activity" label="Activity" />
      </Tabs>
      <Button
        id="detailCloseBtn"
        horizontalAlign="right"
        iconBefore="bold/interface-delete-1"
        styleVariant="outline"
      >
        <Event
          id="f1a2b3c4"
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
        disableSubmit="{{ updateMember.isFetching }}"
        initialData="{{ membersTable.selectedSourceRow }}"
        loading="{{ updateMember.isFetching }}"
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
            id="detailDepartment"
            data="{{ selectDepartments.data }}"
            formDataKey="department"
            itemMode="mapped"
            label="Department"
            labelPosition="top"
            labels="{{ item.label }}"
            showSelectionIndicator={true}
            values="{{ item.value }}"
          />
          <Select
            id="detailRole"
            formDataKey="role"
            itemMode="static"
            label="Role"
            labelPosition="top"
            showSelectionIndicator={true}
          >
            <Option id="r1a1a" value="Engineer" label="Engineer" />
            <Option id="r2b2b" value="Designer" label="Designer" />
            <Option id="r3c3c" value="Manager" label="Manager" />
            <Option id="r4d4d" value="Analyst" label="Analyst" />
            <Option id="r5e5e" value="Lead" label="Lead" />
          </Select>
          <Select
            id="detailStatus"
            formDataKey="status"
            itemMode="static"
            label="Status"
            labelPosition="top"
            showSelectionIndicator={true}
          >
            <Option id="ds1a1" value="active" label="Active" />
            <Option id="ds2b2" value="on_leave" label="On Leave" />
            <Option id="ds3c3" value="offboarded" label="Offboarded" />
          </Select>
          <Date
            id="detailJoinedDate"
            formDataKey="joined_date"
            label="Joined"
            labelPosition="top"
          />
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
          id="d5e6f7a8"
          event="submit"
          method="trigger"
          params={{ ordered: [] }}
          pluginId="updateMember"
          type="datasource"
          waitMs="0"
          waitType="debounce"
        />
      </Form>
    </View>
    <View id="activityView" label="Activity" viewKey="activity">
      <Text
        id="activityPlaceholder"
        value="Activity log for **{{ membersTable.selectedRow.name }}** will appear here.\n\nThis view demonstrates the tabbed detail pane pattern with dynamic width — the Activity tab expands the panel to 550px to accommodate richer content."
        verticalAlign="top"
      />
    </View>
  </Container>
</SplitPaneFrame>
